/* "Request update" button: fire the Daily Brief scheduled task on demand.

   GET  /api/refresh   -> {enabled, needsKey, cooldownMin}  (lets the page decide whether to show the button)
   POST /api/refresh   body {"key": "..."} -> fires the task through its API trigger

   Set these in Vercel (Project > Settings > Environment Variables). Nothing secret lives in the repo.
     ROUTINE_FIRE_URL   the task's API trigger URL, ending in /fire
     ROUTINE_TOKEN      the task's API trigger bearer token
     REFRESH_KEY        optional passcode; when set, the button asks for it once per browser
     REFRESH_COOLDOWN_MIN  optional, default 20: refuse a request this soon after the last update
*/
const crypto = require("crypto");

const COOLDOWN_MIN = Number(process.env.REFRESH_COOLDOWN_MIN || 20);
let lastFire = 0; // per warm instance only; the edition's own timestamp is the main guard

function json(res, code, body) {
  res.statusCode = code;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

function sameKey(a, b) {
  const x = crypto.createHash("sha256").update(String(a)).digest();
  const y = crypto.createHash("sha256").update(String(b)).digest();
  return crypto.timingSafeEqual(x, y);
}

function readBody(req) {
  if (req.body && typeof req.body === "object") return Promise.resolve(req.body);
  return new Promise(resolve => {
    let s = "";
    req.on("data", c => { s += c; if (s.length > 2000) req.destroy(); });
    req.on("end", () => { try { resolve(JSON.parse(s || "{}")); } catch (e) { resolve({}); } });
    req.on("error", () => resolve({}));
  });
}

/* Minutes since the live edition was last published, or null if unknown. */
async function minutesSinceUpdate(host) {
  try {
    const r = await fetch(`https://${host}/data/latest.json?t=${Date.now()}`, { headers: { "Cache-Control": "no-cache" } });
    const d = await r.json();
    const ts = d && d.edition && d.edition.update && d.edition.update.ts;
    return ts ? (Date.now() - Date.parse(ts)) / 60000 : null;
  } catch (e) {
    return null;
  }
}

module.exports = async (req, res) => {
  const url = process.env.ROUTINE_FIRE_URL, token = process.env.ROUTINE_TOKEN, key = process.env.REFRESH_KEY;
  const enabled = !!(url && token && /^https:\/\/api\.anthropic\.com\/.+\/fire$/.test(url));

  if (req.method === "GET") return json(res, 200, { enabled, needsKey: !!key, cooldownMin: COOLDOWN_MIN });
  if (req.method !== "POST") { res.setHeader("Allow", "GET, POST"); return json(res, 405, { error: "Use POST." }); }
  if (!enabled) return json(res, 503, { error: "On-demand updates are not set up yet." });

  // Only accept clicks from the site itself.
  const origin = req.headers.origin || "";
  if (origin && origin !== `https://${req.headers.host}`) return json(res, 403, { error: "Wrong origin." });

  const body = await readBody(req);
  if (key && !sameKey(body.key || "", key)) return json(res, 401, { error: "Wrong passcode." });

  const sinceFire = (Date.now() - lastFire) / 60000;
  const sinceUpd = await minutesSinceUpdate(req.headers.host);
  const since = Math.min(sinceFire, sinceUpd == null ? Infinity : sinceUpd);
  if (since < COOLDOWN_MIN) {
    const wait = Math.ceil(COOLDOWN_MIN - since);
    return json(res, 429, { error: `The brief was updated or requested ${Math.floor(since)} min ago. Try again in about ${wait} min.` });
  }

  const cairo = new Date().toLocaleString("en-GB", { timeZone: "Africa/Cairo", dateStyle: "medium", timeStyle: "short" });
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "anthropic-beta": "experimental-cc-routine-2026-04-01",
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text: `Manual update requested from the website at ${cairo} Cairo.` })
    });
    if (!r.ok) {
      const msg = r.status === 429 ? "The task's hourly run limit is reached. Try again later."
        : r.status === 401 ? "The trigger token is wrong or was rotated. Update ROUTINE_TOKEN in Vercel."
        : `The trigger returned HTTP ${r.status}.`;
      return json(res, 502, { error: msg });
    }
    lastFire = Date.now();
    return json(res, 202, { ok: true, message: "Update requested. A new version usually lands in 20 to 40 minutes; this page checks for it automatically." });
  } catch (e) {
    return json(res, 502, { error: "Could not reach the trigger endpoint." });
  }
};
