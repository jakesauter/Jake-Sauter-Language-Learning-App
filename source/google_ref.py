"""Google Translate reference for every base sentence, gathered a little each day.

Polylang's sentences are written by hand (and by Claude). Google's translation of the same English is kept
next to them as a check: the build shows it under "Google Translate, for comparison", and
google_compare.py lists the sentences where the two disagree most.

The Google key allows 15,000 characters a day (set in Google Cloud), so this spends up to DAILY_BUDGET
characters per Pacific-time day, then stops; cron runs it again after Google's quota resets at midnight
Pacific. Already-fetched sentences are never asked again. The key is read from ~/.config/polylang and is
never written anywhere else.

Usage (from source/): python3 google_ref.py [--budget N] [--dry-run]
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
REF_FILE = os.path.join(HERE, "google_ref.json")
KEY_FILE = os.path.expanduser("~/.config/polylang/google_translate_key")
USAGE_FILE = os.path.expanduser("~/.config/polylang/google_usage.json")
DAILY_BUDGET = 14000          # of Google's 15,000/day; the rest is left for live use in the app
BATCH_CHARS = 1800

# Google's code for each app language, in the order they are filled.
# Cantonese and Mandarin first (only the sentences that have no Google line yet), then the hand-drafted rest.
TARGETS = [("yue", "yue"), ("cmn", "zh-CN"), ("es", "es"), ("fr", "fr"), ("de", "de"),
           ("pt", "pt"), ("tr", "tr"), ("he", "iw"), ("fa", "fa"), ("ar", "ar")]


def pacific_day():
    return datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).date().isoformat()


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)


def base_sentences():
    """English of every card, plus the Google lines the build already has (from the older google*.txt files)."""
    html = open(os.path.join(HERE, "..", "index.html"), encoding="utf-8").read()
    start = html.index("const PHRASES = ") + len("const PHRASES = ")
    phrases, _ = json.JSONDecoder().raw_decode(html[start:])
    return phrases


def translate(texts, target, key):
    body = json.dumps({"q": texts, "source": "en", "target": target, "format": "text"}).encode()
    request = urllib.request.Request("https://translation.googleapis.com/language/translate/v2?key=" + key,
                                     data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        message = json.loads(error.read() or b"{}").get("error", {}).get("message", str(error))
        raise RuntimeError(f"{error.code}: {message}") from None
    return [t["translatedText"] for t in payload["data"]["translations"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=DAILY_BUDGET)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    phrases = base_sentences()
    ref = load(REF_FILE, {})
    usage = load(USAGE_FILE, {})
    today = pacific_day()
    left = args.budget - usage.get(today, 0)
    key = open(KEY_FILE).read().strip()

    queue = []
    for lang, code in TARGETS:
        have = ref.setdefault(lang, {})
        for p in phrases:
            already_in_app = lang in ("yue", "cmn") and p.get("g_" + lang)
            if p["en"] not in have and not already_in_app:
                queue.append((lang, code, p["en"]))
    print(f"{today}: {left} characters left today, {len(queue)} sentences waiting "
          f"({sum(len(e) for _, _, e in queue)} characters)")

    done = 0
    while queue and left > 0:
        lang, code = queue[0][:2]
        batch, size = [], 0
        while queue and queue[0][0] == lang and size + len(queue[0][2]) <= min(BATCH_CHARS, left):
            batch.append(queue.pop(0)[2]); size += len(batch[-1])
        if not batch:
            break
        if args.dry_run:
            print(f"would send {len(batch)} {lang} sentences ({size} chars)"); left -= size; continue
        try:
            out = translate(batch, code, key)
        except RuntimeError as error:
            print("stopped:", error)
            if "limit" in str(error).lower() or "quota" in str(error).lower():
                usage[today] = args.budget            # Google says today's quota is used up
            break
        for english, text in zip(batch, out):
            ref[lang][english] = text
        usage[today] = usage.get(today, 0) + size
        left -= size; done += len(batch)
        save(REF_FILE, ref); save(USAGE_FILE, usage)
        print(f"{lang}: +{len(batch)} ({size} chars), {left} left today")
    print(f"fetched {done} today; {len(queue)} still waiting")


if __name__ == "__main__":
    sys.exit(main())
