# Display, Practice map, share links, account (2026-11-12, evening)

## "Three languages are selected but only two are showing"
- Cause: since the redesign, phones defaulted to a focus view (one language + English) and Display's choices only applied after tapping "Compare all languages".
- Now every language picked under Display shows, on every screen size. "Show only <language>" stays as an opt-in button on each card.
- The setting moved to a new key (`polylang-focus-2`), so phones that had the old default start showing everything.
- Changing a language under Display turns "Show only" off again, because picking languages means wanting to see them.

## Word-by-word map in Practice
- The Practice answer now includes the same word map as the Learn card, under the memory hooks.
- It shows the language being practiced linked to English (two lanes), whatever Display is set to, so the flashcard stays focused.
- `renderDetail(p, { mapOnly, langs })` builds just the map.
- Old maps are released when the next card is shown.

## A link to each phrase
- Each phrase card has a Share button. On phones it opens the share sheet (Messages, Copy, …) with the English, the sentence in the shown language and the link. Elsewhere it copies the link and says "Link copied".
- Links look like `…/Jake-Sauter-Language-Learning-App/#p=how-old-is-he`: the English sentence, lowercased, with hyphens. A phrase whose English repeats in another topic gets `-2`.
- If a phrase's English wording is edited later, its old link stops matching and the app just opens normally.
- Opening a link goes to the phrase's topic, opens its card and scrolls it just below the search bar.
- First-run setup is skipped on that visit, so the person sees the phrase first. They see the default languages.

## Mandarin parallel pass, second round ("look for other mistakes like this")
- Recount after the first pass: 38 cards still grouped words differently.
- Fixed 19 by adding the spoken question particle 啊 where Cantonese ends with 呀, so the "(question)" word links up (你忙不忙啊, 你会不会煮饭啊), plus 吧 for 啦 in "I'll make the coffee".
- The other 19 are Mandarin grammar and stay:
  - 左转 / 右转
  - 先 before the verb
  - 把 in "Don't burn the rice"
  - 多 before the verb
  - no equivalent of 啲
  - 你叫什么名字

## Account
- Created the home-server account `jakesauter`; the password is stored only as the server's salted scrypt hash.
- Moved the 13 conversations recorded as the Tailscale guest (jakesauter@github) into it.
- Left 3 conversations under "local": they were made on the desktop itself, including a sample-audio test. The server never moves "local" ones into accounts.
- Backup of the account database before the change: `/mnt/storage/polylang-data/accounts.sqlite3.bak-2026-11-12`.
- To see the recordings on a phone: Record → sign in as jakesauter.
- A new recovery code can be made from the account screen (none was shown during this out-of-app creation).
