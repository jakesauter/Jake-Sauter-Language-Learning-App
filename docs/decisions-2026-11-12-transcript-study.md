# Transcripts teach both ways (2026-11-12)

Feedback: "The transcript should have the source language and the translation, not just the target language. It should be a learning tool." The Recordings transcript showed English lines alone; only Chinese lines had a translation (into English).

## What changed

- Every English line now also shows the same sentence in the language being learned, with the word strip (sound, character, meaning for each word). Chinese lines still show the Chinese, the word strip and the English, as before.
- Live sessions: the app sends `study=<language>` when it connects. The home server translates each English line right after it is heard (HY-MT 1.8B on the card, about 0.2 s a line), sends a `study` message, and saves `study` / `study_language` with the line.
- Older saved conversations: when one is opened, the app asks `POST /conversations/{id}/study` for the English lines that have no translation yet (40 at a time). The server caches them in `study.json` in the conversation folder, so each line is translated once. `lines.jsonl` is never rewritten, so this can't clash with a live session appending to the same conversation.

## Decisions made without asking

- **Taishanese learners see Cantonese.** No available model writes Taishanese, so English lines are translated into Cantonese, labelled "Cantonese" (not presented as Taishanese). Mandarin learners get Mandarin.
- **Which language is "being learned":** the language picked for recording (`polygrok-rec-lang`, e.g. Taishanese, Cantonese, Mandarin). If a session sends none, the server uses the first of Taishanese/Cantonese/Mandarin among the conversation's languages.
- **Pronoun clean-up, translations only:** the small translator sometimes writes Mandarin pronouns inside Cantonese (她, 他們). Translations get 佢 / 佢哋 / 我哋 / 你哋; 其他 ("other") is left alone. What people actually said is never altered.
- **Known limit:** translation quality is the 1.8B model's. Some lines come out more formal than people talk (我應該買嗎 instead of 我應唔應該買呀), and an unusual character form (枴杖 "cane") can appear without a word-strip reading.
- The "…" placeholder disappears if a translation fails, rather than waiting forever.
