# Polylang roadmap

## Focus now
Taishanese, Cantonese, Mandarin and English: deepen the sentences, fix Taishanese words marked `?`, and grow the recorder into a family-voice corpus.

## Added languages (switched off by default; turn on with the chips at the top)
Portuguese (Brazil), Persian (spoken Tehrani + written), Arabic (Levantine word by word; Egyptian and MSA as full sentences), Hebrew, Turkish.

- Done: all 492 sentences (`source/me/00–10.txt`; 360–491 added 2026-11-13).
- All machine-drafted by Claude. Check with native speakers or paste Google Translate batches to compare.
- Before building, `cd source && python3 me/check_me.py ../index.html` checks every block: sentence numbers and English, all eight lines present, refs inside the English chunks, transliterations on fa/la/he tokens.

## Format (one block per sentence, keyed by index)
    = 360 Do you like your teacher?
    pt: Você/0 ; gosta do/1 ; seu/2 ; professor/3
    fa: معلمتو{moallemet-o}/2,3 ; دوست داری{dust dāri}/0,1
    fw: written Persian sentence || transliteration
    la: Levantine tokens{translit}/refs
    eg: Egyptian sentence || transliteration
    ms: MSA sentence || transliteration
    he: Hebrew tokens{translit}/refs
    tr: Turkish/refs
The numbers after `/` point at the English chunks shown under each card, so the connector lines know what to link.

## Adding a language (toward 20+)
1. Add its code to `LANES`, `NAMES`, `NATIVE`, the voice table and the View checkbox (see `patches/mideast.py`).
2. Add a tag to `ME_TOK` in `build2.py` and write `me/*.txt` lines for it.
3. Optional: a Rules and roots section (sound shifts, core grammar, writing system) and cognate hooks.

Candidate next languages: Japanese, Korean, Vietnamese, Hindi/Urdu, Russian, Italian, Tagalog.

## Learning-science backlog
- Rules and roots sections for Persian, Arabic, Hebrew, Turkish and Portuguese (triliteral roots k-t-b and s-l-m / sh-l-m; Persian cognates such as mādar/mother, barādar/brother, nām/name; Turkish suffix stacking and vowel harmony).
- "Survival deck": a fast first 100 sentences, modeled on the Defense Language Institute's Headstart course.
- Reading list additions: FSI difficulty categories and DLI course lengths.
