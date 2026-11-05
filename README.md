# Family Phrasebook

A phone-friendly phrasebook for everyday family conversation in **Taishanese, Cantonese and Mandarin**, broken down word by word.

**Open the app:** https://jakesauter.github.io/Jake-Sauter-Language-Learning-App/

## What it does

- Everyday sentences grouped by topic, each shown as interlinear word rows (Taishanese, Cantonese, English, Mandarin) with lines linking each word to its meaning
- Tap any word to hear it and see what it means, including grammar words like 得, 呀 and 咗
- Play a whole sentence from the button at the start of each row: device voices for Cantonese and Mandarin, and a built-in JavaScript tone synthesizer for all three
- Easy English spelling by default, with Jyutping, pinyin and Stephen Li's Taishanese romanization available under View
- Type any English sentence for a word-by-word build from the built-in dictionary

The whole app is one self-contained `index.html`.

## Building

`source/` holds the sentence data and build scripts. `python3 source/build2.py index.html` rebuilds the page from `page.html`, the sentence files and the word table.

## Sources

- Taishanese: Stephen Li's Taishanese dictionary
- CC-CEDICT, Rime Cantonese (Jyutping), OpenCC, pinyin-data and Jieba word frequencies
- Google Translate output is shown on saved sentences for comparison
