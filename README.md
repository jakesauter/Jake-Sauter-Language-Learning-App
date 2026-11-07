![Polyling](banner.png)

# Polyling

*Polyglot + grok: understand a language deeply, word by word.*

A phone-friendly guide to everyday family conversation, broken down word by word in **Taishanese, Cantonese, English, Mandarin, Spanish, French and German**.

**Open the app:** https://jakesauter.github.io/Jake-Sauter-Language-Learning-App/

## What it does

- Everyday sentences grouped by topic (including Talking About the Day and Joking Around), each shown as interlinear word rows with lines linking each word to its meaning
- One-tap switches at the top to show or hide any language
- Tap any word to hear it and see what it means, including grammar words like 得, 呀, 咗, ne … pas and lass uns
- Play a whole sentence from the button at the start of each row: device voices for Cantonese, Mandarin, Spanish, French and German, and a built-in Taishanese speech synthesizer
- Six themes, from Paper (white) to Night (black)
- The interface itself can be switched to English, Español, Français, Deutsch, 廣東話, 普通话 or 台山話
- Easy English spelling by default, with Jyutping, pinyin and Stephen Li's Taishanese romanization available under View
- Type any English sentence and a built-in sentence composer rebuilds it in each language's own grammar: Chinese word order, aspect and question particles, and Spanish, French and German conjugation, articles and word order
- A full-sentence section under every card, with a full-screen view to show someone who speaks only that language
- **Record** family and friends, then work through it slowly: mark moments, loop them at 0.5× speed, write what you hear and what it means, and save voice clips to your phrasebook. Recordings stay on the phone. Live captions use the phone's own speech recognition where the browser allows it, and an optional home server (`server/`) transcribes and translates on your own GPU, with no cloud bill
- Every Chinese character in explanations shows its pronunciation above it (Rime Cantonese dictionary, CC BY 4.0)
- **My phrasebook**: save the sentences you actually need (including ones you translate yourself), mark what you already know, and copy the whole list as text

## Built on learning science

Polyling is designed for adults who already speak one language and are learning another.

- **Practice** uses retrieval (say it before you see it), spaced repetition, the production effect (say it aloud), interleaving, and a sleep-aware schedule
- **Tone trainer**: high-variability phonetic training with pitch-shape pictures
- **Memory hooks**: sound bridges to languages you know (下雨 xià yǔ ↔ Spanish lluvia), character stories, cognates, and a box for your own hooks
- **Rules and roots**: automatic character breakdowns (媽 = 女 woman + 馬 maa, a sound hint), sound shifts between languages (Cantonese s → Taishanese ɬ, English t → German z), and each language's core rules
- **Your day**: what to do in the morning, through the day, at family meals, in the evening and before bed
- **Reading list**: key books in language pedagogy, learning science and linguistic anthropology, plus arXiv papers on spaced repetition, cognates and tone training

The whole app is one self-contained `index.html`.

## Taishanese voice

No phone ships a Taishanese voice, so `source/tsn_voice.js` is a source-filter (Klatt-style) speech synthesizer written for Stephen Li's romanization. It builds each syllable from its initial, final and Chao tone digits. That includes aspirated and unaspirated stops, the lateral fricative ɬ, nasal and stop codas, and the rising changed tones. It renders a WAV in the browser and plays it through an audio element, so it works with the phone on silent.

## Building

`source/` holds the sentence data and build scripts:

    python3 source/build2.py built.html
    python3 source/wrap_site.py built.html index.html site

## Sources

- Taishanese: Stephen Li's Taishanese dictionary
- CC-CEDICT, Rime Cantonese (Jyutping), OpenCC, pinyin-data and Jieba word frequencies
- Spanish, French and German written for this guide
- Google Translate output is shown on saved sentences for comparison
