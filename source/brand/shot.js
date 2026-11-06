const { chromium } = require("playwright");
const fs = require("fs");
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  for (const [src, out, w, h] of JSON.parse(process.argv[2])) {
    await p.setViewportSize({ width: w, height: h });
    const svg = fs.readFileSync(src, "utf8").replace("<svg ", `<svg width="${w}" height="${h}" `);
    await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await p.waitForTimeout(150);
    await p.screenshot({ path: out, omitBackground: true, clip: { x: 0, y: 0, width: w, height: h } });
  }
  await b.close();
})();
