# Polygrok

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
- Type any English sentence for a word-by-word build from the built-in dictionary

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
