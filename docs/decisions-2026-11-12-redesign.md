# Redesign decisions, 12 November 2026

Jake approved the UX review (https://claude.ai/artifact/9QcApoMMpZxUyNiyeWdHUF) and asked for all of it to be built and published without questions. These are the calls made along the way.

## Built
1. **One topic at a time.** The main page shows the topic list; tapping a topic shows only its sentences with an "All topics" link back. The page went from about 57,800 pixels tall to about 2,000. Search still looks across every topic.
2. **Bottom tab bar** (Learn, Practice, Phrasebook, Record) on the main page and inside those three screens, which are full-screen on phones. Tabs are ignored while a recording is running so a stray tap cannot stop it.
3. **Today card** replaces the three buttons: one Start/Continue button that goes straight into today's session.
4. **First-run setup** for new users only: which languages to learn, and the app language. People who already have saved settings never see it. "Run setup again" is at the bottom of Display.
   - Jake asked to remove "How much time a day?", so it is gone. The existing "New sentences per day" choice inside Practice is unchanged.
5. **Focus view** for sentences: on phones the diagram shows the language being practiced plus English at a larger size, with "Compare all languages" underneath. Wider screens start with all languages. The choice is remembered.
6. **Practice screen:** the eleven language chips became one drop-down; the four counters became a sentence ("8 new sentences", "34 sentences learned · 2-day streak").
7. **Record screen:** the Start button is first; languages sit in a collapsed section; the "Connecting for live translation… (Tailscale needs to be on)" line no longer shows on opening.
8. **Small fixes:** language chips are 44 pixels tall; "View" is now "Display"; the language chips moved from the home screen into Display; zeros are drawn without a slash; topic list shows "learned / total" once you have learned something in a topic.
9. **Desktop (1100 pixels and wider):** topics stay in a left column, sentences on the right.

## Not built, and why
- **Separate search icon** (search and translate still share one box): the box drives both features in the code and splitting it risked breaking translate.
- **Right-hand word-details pane on desktop:** word details still open under the diagram.
- **Tone colours, "say it" check, family voices in practice, share-as-image, install prompt:** these were listed as ideas, not as approved changes.
- **Long sentences in focus view scroll sideways** instead of wrapping, because the connector lines assume one row per language.

## To check
- New interface text was written in English and Cantonese (also used for the Taishanese interface). The Cantonese is Claude's and should be read by a native speaker. Other interface languages fall back to English for the new labels.
- Tested in Chromium at iPhone and desktop sizes only; not yet on a real iPhone.
- The private copy served from the home machine was refreshed, but its server is currently stopped (see the trading notes), so that copy is offline until `systemctl --user start polylang-home.service`.
