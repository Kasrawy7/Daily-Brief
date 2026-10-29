#!/usr/bin/env node
/* Render the site in headless Chromium and fail on anything a reader would notice.
   node scripts/smoke.js                 serve this folder locally and test it
   node scripts/smoke.js <url> [iso]     test a live URL; with iso, also require that edition date */
const http = require("http"), fs = require("fs"), path = require("path");
const { chromium } = require("playwright");
const ROOT = path.resolve(__dirname, "..");
const TYPES = { ".html": "text/html", ".json": "application/json", ".js": "text/javascript", ".css": "text/css" };

function serve() {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      let p = decodeURIComponent(req.url.split("?")[0]);
      if (p.endsWith("/")) p += "index.html";
      const f = path.join(ROOT, path.normalize(p));
      if (!f.startsWith(ROOT) || !fs.existsSync(f)) { rsp.writeHead(404); return rsp.end(); }
      rsp.writeHead(200, { "Content-Type": TYPES[path.extname(f)] || "application/octet-stream" });
      fs.createReadStream(f).pipe(rsp);
    }).listen(0, () => res(srv));
  });
}

(async () => {
  let url = process.argv[2], wantIso = process.argv[3], srv = null;
  if (!url) { srv = await serve(); url = `http://localhost:${srv.address().port}/`; }
  const expected = JSON.parse(fs.readFileSync(path.join(ROOT, "data/latest.json"), "utf8"));
  const browser = await chromium.launch();
  const problems = [];
  for (const [name, viewport] of [["desktop", { width: 1280, height: 900 }], ["phone", { width: 390, height: 844 }]]) {
    const page = await browser.newPage({ viewport });
    const errs = [];
    page.on("pageerror", e => errs.push(e.message));
    page.on("console", m => { if (m.type() === "error") errs.push(m.text()); });
    await page.goto(url, { waitUntil: "networkidle" });
    await page.waitForTimeout(600);
    const r = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      edition: (document.getElementById("edline") || {}).innerText || "",
      loadError: !!document.querySelector(".wrap > p.empty"),
      tops: document.querySelectorAll("#tops li").length,
      kpis: document.querySelectorAll("#kpis .tile").length,
      cards: document.querySelectorAll("#cards .card").length,
      charts: document.querySelectorAll(".chart").length,
      emptyViz: [...document.querySelectorAll(".chart .viz")].filter(v => !v.innerHTML.trim()).length,
      idx: document.querySelectorAll("#idx .ix").length,
      rows: document.querySelectorAll("#stkBody tr").length,
      sources: document.querySelectorAll("#src li").length
    }));
    const tag = s => problems.push(`${name}: ${s}`);
    errs.forEach(e => tag("script error: " + e));
    if (r.loadError) tag("the edition failed to load");
    if (r.overflow > 1) tag(`page scrolls sideways by ${r.overflow}px`);
    if (r.tops < 3) tag(`only ${r.tops} top stories`);
    if (r.kpis !== 6) tag(`${r.kpis} headline tiles, expected 6`);
    if (r.cards !== expected.stories.length) tag(`${r.cards} story cards, data has ${expected.stories.length}`);
    if (r.emptyViz) tag(`${r.emptyViz} chart(s) drew nothing`);
    if (r.idx < 1) tag("no index cards in the EGX section");
    if (r.rows !== expected.stocks.equities.length) tag(`${r.rows} stock rows, data has ${expected.stocks.equities.length}`);
    if (!r.edition.includes(expected.edition.date)) tag(`shows "${r.edition.split("\n")[0]}", expected ${expected.edition.date}`);
    console.log(`${name}: ${r.cards} stories, ${r.charts} charts, ${r.rows} stocks, ${r.sources} sources, sideways scroll ${r.overflow}px`);
    await page.close();
  }
  if (wantIso && expected.edition.iso !== wantIso) problems.push(`local latest.json is ${expected.edition.iso}, expected ${wantIso}`);
  await browser.close();
  if (srv) srv.close();
  if (problems.length) { console.log("SMOKE FAILED\n  " + problems.join("\n  ")); process.exit(1); }
  console.log("SMOKE OK: " + url);
})().catch(e => { console.error("SMOKE FAILED: " + e.message); process.exit(1); });
