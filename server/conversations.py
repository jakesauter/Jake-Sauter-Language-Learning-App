"""Conversations saved on this computer, one folder per person.

The person is the Tailscale login that `tailscale serve` attaches to every request (only Tailscale can
set it, and nothing reaches this server except through Tailscale). Requests made on this computer
itself, such as tests, belong to "local".

    /data/people/<person id>/conversations/<conversation id>/
        conversation.json    title, languages, created/updated times
        lines.jsonl          one finished line per row, appended as they happen
        recordings/          one WAV per recording session
"""

import hashlib
import json
import os
import re
import secrets
import time

import accounts

DATA_FOLDER = os.environ.get("POLYLANG_DATA", "/data")
CONVERSATION_ID = re.compile(r"[A-Za-z0-9_-]{8,32}")


DEVICE_ID = re.compile(r"[A-Za-z0-9_-]{16,64}")


def person_from(headers, device_id=""):
    """Signed-in account first, then the Tailscale login, then the anonymous ID kept on the device."""
    account = accounts.account_for_token(accounts.bearer_token(headers))
    if account:
        return f"account:{account['id']}"
    login = headers.get("tailscale-user-login")
    if login:
        return login
    device_id = headers.get("x-polylang-device") or device_id or ""
    return "device:" + device_id if DEVICE_ID.fullmatch(device_id) else "local"


def move_everything(from_person, to_person):
    """When a guest signs in, their device's conversations join the account."""
    if from_person == to_person or from_person == "local":
        return 0
    source_root = os.path.join(person_folder(from_person), "conversations")
    target_root = os.path.join(person_folder(to_person), "conversations")
    os.makedirs(target_root, exist_ok=True)
    moved = 0
    for conversation_id in os.listdir(source_root) if os.path.isdir(source_root) else []:
        if CONVERSATION_ID.fullmatch(conversation_id) and not os.path.exists(os.path.join(target_root, conversation_id)):
            os.replace(os.path.join(source_root, conversation_id), os.path.join(target_root, conversation_id))
            moved += 1
    return moved


def person_folder(person):
    person_id = hashlib.sha256(person.encode()).hexdigest()[:16]
    folder = os.path.join(DATA_FOLDER, "people", person_id)
    os.makedirs(folder, exist_ok=True)
    owner_file = os.path.join(folder, "person.json")
    if not os.path.exists(owner_file):
        with open(owner_file, "w") as file:
            json.dump({"login": person}, file)
    return folder


def conversation_folder(person, conversation_id):
    if not CONVERSATION_ID.fullmatch(conversation_id or ""):
        raise ValueError("bad conversation id")
    folder = os.path.join(person_folder(person), "conversations", conversation_id)
    if not os.path.realpath(folder).startswith(os.path.realpath(DATA_FOLDER) + os.sep):
        raise ValueError("bad conversation id")
    return folder


def create(person, title, languages):
    conversation_id = secrets.token_urlsafe(9)
    folder = conversation_folder(person, conversation_id)
    os.makedirs(os.path.join(folder, "recordings"), exist_ok=True)
    now = time.time()
    details = {"id": conversation_id, "title": title.strip()[:120] or time.strftime("Conversation %b %d, %H:%M"),
               "languages": languages, "created": now, "updated": now, "line_count": 0}
    _write_details(folder, details)
    return details


def exists(person, conversation_id):
    try:
        return os.path.isfile(os.path.join(conversation_folder(person, conversation_id), "conversation.json"))
    except ValueError:
        return False


def details(person, conversation_id):
    with open(os.path.join(conversation_folder(person, conversation_id), "conversation.json")) as file:
        return json.load(file)


def list_for(person):
    root = os.path.join(person_folder(person), "conversations")
    if not os.path.isdir(root):
        return []
    found = []
    for conversation_id in os.listdir(root):
        try:
            found.append(details(person, conversation_id))
        except (OSError, ValueError):
            continue
    return sorted(found, key=lambda conversation: conversation["updated"], reverse=True)


def lines(person, conversation_id):
    path = os.path.join(conversation_folder(person, conversation_id), "lines.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as file:
        return [json.loads(row) for row in file if row.strip()]


def append_line(person, conversation_id, line):
    folder = conversation_folder(person, conversation_id)
    with open(os.path.join(folder, "lines.jsonl"), "a", encoding="utf-8") as file:
        file.write(json.dumps(line, ensure_ascii=False) + "\n")
    conversation = details(person, conversation_id)
    conversation["updated"] = time.time()
    conversation["line_count"] = conversation.get("line_count", 0) + 1
    _write_details(folder, conversation)


def study_translations(person, conversation_id):
    """Cached translations of a conversation's English lines into study languages: {language: {text: translation}}."""
    try:
        with open(os.path.join(conversation_folder(person, conversation_id), "study.json"), encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return {}


def save_study_translations(person, conversation_id, cache):
    folder = conversation_folder(person, conversation_id)
    temporary_path = os.path.join(folder, "study.json.tmp")
    with open(temporary_path, "w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False)
    os.replace(temporary_path, os.path.join(folder, "study.json"))


def recording_path(person, conversation_id):
    folder = os.path.join(conversation_folder(person, conversation_id), "recordings")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, time.strftime("%Y-%m-%d_%H%M%S") + ".wav")


def rename(person, conversation_id, title):
    folder = conversation_folder(person, conversation_id)
    conversation = details(person, conversation_id)
    conversation["title"] = title.strip()[:120] or conversation["title"]
    _write_details(folder, conversation)
    return conversation


def _write_details(folder, conversation):
    temporary_path = os.path.join(folder, "conversation.json.tmp")
    with open(temporary_path, "w") as file:
        json.dump(conversation, file, ensure_ascii=False, indent=1)
    os.replace(temporary_path, os.path.join(folder, "conversation.json"))
