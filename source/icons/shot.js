const { chromium } = require("playwright");
const fs = require("fs");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  const jobs = JSON.parse(process.argv[2]);
  for (const [src, out, size] of jobs) {
    await p.setViewportSize({ width: size, height: size });
    const svg = fs.readFileSync(src, "utf8");
    await p.setContent(`<html><body style="margin:0;background:transparent">${svg.replace("<svg ", `<svg width="${size}" height="${size}" `)}</body></html>`);
    await p.screenshot({ path: out, omitBackground: true, clip: { x: 0, y: 0, width: size, height: size } });
  }
  await b.close();
})();
