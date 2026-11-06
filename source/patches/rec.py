p = "page.html"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

rec = open("record.js", encoding="utf-8").read()
rep("  const noteHtml = t => esc(t).replace(", "  const noteHtml = t => zhRuby(esc(t)).replace(")
rep("  /* search + translate */", rec + "\n\n  /* search + translate */")
rep('''      <button class="book-cta" id="book-btn" type="button"></button>''', '''      <button class="book-cta" id="book-btn" type="button"></button>
      <button class="book-cta" id="rec-btn" type="button"><svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM5 11a7 7 0 0 0 14 0M12 18v3" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg><span data-i18n="r_btn">Record</span></button>''')
rep('''  $("book-btn").addEventListener("click", () => Book.open());''', '''  $("book-btn").addEventListener("click", () => Book.open());
  $("rec-btn").addEventListener("click", () => Rec.open());''')
rep('''  .now-tip { ''', '''  .rec-form { display: grid; gap: var(--s-3); }
  .rec-l { display: grid; gap: 4px; font-size: var(--t-xs); font-weight: 700; color: var(--muted); }
  .rec-in { font: inherit; font-size: 1rem; font-weight: 400; color: var(--ink); background: var(--wash); border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; width: 100%; box-sizing: border-box; }
  .rec-check { display: flex; gap: 10px; align-items: flex-start; font-size: var(--t-sm); color: var(--ink-2); }
  .rec-check input { width: 20px; height: 20px; margin: 1px 0 0; accent-color: var(--ink); flex: none; }
  .rec-go { justify-content: center; }
  .rec-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
  .rec-row { width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 12px 14px; border: 1px solid var(--line); border-radius: 12px; background: var(--paper); color: var(--ink); font: inherit; text-align: left; cursor: pointer; }
  .rec-row span:first-child { display: grid; gap: 2px; min-width: 0; }
  .rec-row small, .rec-meta { color: var(--muted); font-size: var(--t-xs); }
  .rec-meta { flex: none; font-variant-numeric: tabular-nums; }
  .rec-home summary { cursor: pointer; font-size: var(--t-sm); color: var(--ink-2); }
  .rec-home-row { display: flex; gap: 6px; margin-top: 8px; }
  .rec-alert { margin: 0; padding: 10px 12px; border: 1px solid var(--ink); border-radius: 10px; font-size: var(--t-sm); }
  .rec-live { display: flex; align-items: center; gap: 12px; }
  .rec-live b { font-size: 2rem; font-variant-numeric: tabular-nums; }
  .rec-live canvas { flex: 1; min-width: 0; height: 36px; color: var(--ink); }
  .rec-dot { width: 14px; height: 14px; border-radius: 50%; background: var(--ink); animation: recblink 1.2s infinite; flex: none; }
  @keyframes recblink { 50% { opacity: 0.2; } }
  .rec-acts { display: grid; gap: 8px; }
  .sq { display: inline-block; width: 14px; height: 14px; background: currentColor; border-radius: 2px; flex: none; }
  .rec-stop .sq { width: 22px; height: 22px; }
  .rec-caps { display: grid; gap: 6px; padding: 12px 14px; background: var(--wash); border-radius: 12px; min-height: 60px; font-size: 1.1rem; }
  .rec-caps p { margin: 0; }
  .rec-caps .interim { color: var(--muted); }
  .rec-player { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 12px; border: 1px solid var(--line); border-radius: 14px; }
  .rec-play { display: inline-flex; align-items: center; gap: 8px; }
  .rec-play svg { width: 18px; height: 18px; }
  .rec-seek { flex: 1 1 100%; accent-color: var(--ink); }
  .rec-tm { font-size: var(--t-xs); color: var(--muted); font-variant-numeric: tabular-nums; }
  .rec-speeds { display: flex; gap: 4px; margin-left: auto; }
  .rec-marks, .rec-lines { display: grid; gap: 10px; }
  .rec-mark { display: grid; gap: 8px; padding: 12px; border: 1px solid var(--line); border-radius: 12px; }
  .rec-mark-head { display: flex; align-items: center; gap: 6px; }
  .rec-mark-head .link { margin-left: auto; font-size: 1.3rem; padding: 0 6px; }
  .rec-mark .pbtn svg, .rec-line .pbtn svg { width: 14px; height: 14px; }
  .pbtn.on { border-color: var(--ink); background: var(--ink); color: var(--paper); }
  .rec-gloss { display: flex; flex-wrap: wrap; gap: 4px 10px; }
  .rec-gloss:empty { display: none; }
  .gl { display: grid; justify-items: center; line-height: 1.2; }
  .gl b { font-weight: 600; font-size: 1.1rem; }
  .gl small { font-size: 0.7rem; color: var(--muted); }
  .rec-line { display: grid; grid-template-columns: auto 1fr; gap: 10px; align-items: start; }
  .rec-line-tx p { margin: 0 0 4px; }
  .rec-line-tx .link { font-size: var(--t-xs); }
  .clip-item { display: grid; grid-template-columns: auto 1fr auto; gap: 10px; align-items: start; padding: 12px 0; }
  .clip-item .pbtn svg { width: 14px; height: 14px; }
  .clip-tx { display: grid; gap: 4px; }
  .clip-said { font-size: 1.15rem; }
  .clip-tx small { color: var(--muted); display: inline-flex; align-items: center; gap: 4px; }
  .clip-tx small .ico { width: 13px; height: 13px; }
  .now-tip { ''')
open(p, "w", encoding="utf-8").write(s)
print("rec ok")
