// Records effects from examples/web/effects-gallery.html as looping GIFs.
// The page clock is driven frame by frame (not screen-recorded), so every GIF is smooth
// and evenly timed regardless of machine speed.
//
//   node tools/capture_gifs.mjs --tier 5 --tier 6          # every effect in tiers 5 and 6
//   node tools/capture_gifs.mjs holo crystal --seconds 3   # named effects
// Options: --out DIR (default media/gifs) --fps 24 --seconds 2.5 --width 480 --scale 2
// Needs Node, Playwright + Chromium and ffmpeg on PATH.
import { mkdirSync, rmSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); } catch { ({ chromium } = await import("playwright")); }

const root = resolve(new URL("..", import.meta.url).pathname);
const page_ = join(root, "examples/web/effects-gallery.html");
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf("--" + k); return i >= 0 ? args[i + 1] : d; };
const tiers = args.flatMap((a, i) => (a === "--tier" ? [Number(args[i + 1])] : []));
const named = args.filter((a, i) => !a.startsWith("--") && !(i > 0 && args[i - 1].startsWith("--")));
const out = resolve(opt("out", join(root, "media/gifs")));
const fps = Number(opt("fps", 24)), seconds = Number(opt("seconds", 2.5)), width = Number(opt("width", 480)), scale = Number(opt("scale", 2));

// read the tier table straight from the page so this never drifts from it
const src = readFileSync(page_, "utf8");
const tierIds = {};
for (const m of src.matchAll(/\{ n: (\d), name: "([^"]+)"[\s\S]*?ids: \[([^\]]+)\]/g))
  tierIds[m[1]] = { name: m[2], ids: [...m[3].matchAll(/"([a-z0-9]+)"/g)].map(x => x[1]) };
const jobs = [...tiers.flatMap(t => (tierIds[t]?.ids || []).map(id => ({ id, tier: t }))),
  ...named.map(id => ({ id, tier: Object.keys(tierIds).find(t => tierIds[t].ids.includes(id)) || "x" }))];
if (!jobs.length) { console.log("Nothing to capture. Use --tier N or effect ids. Tiers:", Object.entries(tierIds).map(([k, v]) => `${k} ${v.name}`).join(" · ")); process.exit(1); }

mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const frames = Math.round(fps * seconds), step = 1000 / fps;
for (const { id, tier } of jobs) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: scale });
  // a manual clock: rAF callbacks only run when we step
  await page.addInitScript(() => {
    let T = 1000; const q = [];
    performance.now = () => T;
    window.requestAnimationFrame = cb => { q.push(cb); return q.length; };
    window.__step = ms => { T += ms; const run = q.splice(0); for (const f of run) f(T); };
  });
  const errors = [];
  page.on("pageerror", e => errors.push(String(e)));
  await page.goto(pathToFileURL(page_).href + "?only=" + id);
  const cv = await page.$(`canvas[data-id="${id}"]`);
  if (!cv) { console.log("skip", id, "(not in the gallery)"); await page.close(); continue; }
  await cv.scrollIntoViewIfNeeded();
  await page.evaluate(ms => { for (let i = 0; i < 20; i++) window.__step(ms); }, step); // warm-up so the loop starts mid-motion
  const dir = join(out, `.frames-${id}`); rmSync(dir, { recursive: true, force: true }); mkdirSync(dir);
  for (let f = 0; f < frames; f++) {
    await page.evaluate(ms => window.__step(ms), step);
    await cv.screenshot({ path: join(dir, String(f).padStart(4, "0") + ".png") });
  }
  const gif = join(out, `tier${tier}-${id}.gif`);
  execFileSync("ffmpeg", ["-v", "error", "-y", "-framerate", String(fps), "-i", join(dir, "%04d.png"),
    "-vf", `scale=${width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192:stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle`,
    "-loop", "0", gif]);
  rmSync(dir, { recursive: true, force: true });
  console.log(`${errors.length ? "WARN" : "ok  "} ${gif.replace(root + "/", "")} ${(statSync(gif).size / 1024).toFixed(0)} KB${errors.length ? " " + errors[0] : ""}`);
  await page.close();
}
await browser.close();
