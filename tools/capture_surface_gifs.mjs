// Records surfacebake techniques as looping GIFs from the two labs, frame by frame on a fixed
// clock (window.__sb / window.__dl capture hooks), so every GIF is smooth and deterministic.
//
//   node tools/capture_surface_gifs.mjs                 # every job below
//   node tools/capture_surface_gifs.mjs frost dissolve  # jobs whose name contains a word
// Options: --out DIR (default media/gifs/surfaces) --fps 15 --width 320
// Needs Node, Playwright + Chromium and ffmpeg on PATH.
import { mkdirSync, rmSync, writeFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); } catch { ({ chromium } = await import("playwright")); }

const root = resolve(new URL("..", import.meta.url).pathname);
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf("--" + k); return i >= 0 ? args[i + 1] : d; };
const words = args.filter((a, i) => !a.startsWith("--") && !(i > 0 && args[i - 1].startsWith("--")));
const out = resolve(opt("out", join(root, "media/gifs/surfaces")));
const fps = Number(opt("fps", 15)), width = Number(opt("width", 320));

// name, page, seconds, and the capture setup. Motions loop on their own clocks; reactive jobs
// script their hits (random visible texels from a fixed seed).
const hitsEvery = (dt, until, frost) => Array.from({ length: Math.floor(until / dt) }, (_, i) => ({ t: 0.15 + i * dt, frost }));
const JOBS = [
  // the same motion on different surfaces
  ["dissolve-painted-crate", "sb", 4.5, { recipe: "Painted metal", mesh: "Crate", motion: "Dissolve", spin: 0.25 }],
  ["dissolve-marble-sphere", "sb", 4.5, { recipe: "Marble", mesh: "Sphere", motion: "Dissolve", spin: 0.25 }],
  ["dissolve-gold-torus", "sb", 4.5, { recipe: "Gold", mesh: "Torus", motion: "Dissolve", spin: 0.25, pitch: -0.7 }],
  ["dissolve-wood-barrel", "sb", 4.5, { recipe: "Wood", mesh: "Barrel", motion: "Dissolve", spin: 0.25 }],
  ["frost-lava-sphere", "sb", 5, { recipe: "Lava rock", mesh: "Sphere", motion: "Frost spread", spin: 0.2 }],
  ["frost-copper-barrel", "sb", 5, { recipe: "Copper patina", mesh: "Barrel", motion: "Frost spread", spin: 0.2 }],
  ["frost-wood-crate", "sb", 5, { recipe: "Wood", mesh: "Crate", motion: "Frost spread", spin: 0.2 }],
  ["frost-gold-torus", "sb", 5, { recipe: "Gold", mesh: "Torus", motion: "Frost spread", spin: 0.2, pitch: -0.7 }],
  ["runes-runestone-crate", "sb", 4, { recipe: "Rune stone", mesh: "Crate", motion: "Rune pulse", spin: 0.3 }],
  ["lavaflow-lavarock-sphere", "sb", 4, { recipe: "Lava rock", mesh: "Sphere", motion: "Lava flow", spin: 0.3 }],
  ["scan-scifi-crate", "sb", 4, { recipe: "Sci-fi panel", mesh: "Crate", motion: "Scan", spin: 0.3 }],
  ["scan-marble-sphere", "sb", 4, { recipe: "Marble", mesh: "Sphere", motion: "Scan", spin: 0.3 }],
  // reactive: hits, effects fighting each other, motion-driven
  ["react-molten-iron-barrel", "sb", 4.5, { recipe: "Rusted iron", mesh: "Barrel", reactive: "Molten hits", spin: 0.3, hits: hitsEvery(0.45, 3.6, false) }],
  ["react-molten-gold-torus", "sb", 4.5, { recipe: "Gold", mesh: "Torus", reactive: "Molten hits", spin: 0.3, pitch: -0.7, hits: hitsEvery(0.35, 3.8, false) }],
  ["react-ice-vs-lava-sphere", "sb", 6, { recipe: "Lava rock", mesh: "Sphere", reactive: "Ice vs lava", spin: 0.25, hits: hitsEvery(1.3, 4.5, true) }],
  ["react-forcefield-spin-sphere", "sb", 5, { recipe: "Sci-fi panel", mesh: "Sphere", reactive: "Force field", spin: 0.2, wobble: 1.4, hits: hitsEvery(0.8, 4.5, false) }],
  // depth tricks
  ["depth-pom-window", "dl:pom", 4, {}],
  ["depth-interior-facade", "dl:interior", 4, {}],
  ["depth-infinite-zoom", "dl:zoom", 3.4, { fps: 12, width: 260, colors: 96 }],
  ["depth-shell-fur", "dl:shells", 4, {}],
  ["depth-layered-parallax", "dl:layers", 4, {}],
].filter(([name]) => !words.length || words.some(w => name.includes(w)));

mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const pages = { sb: join(root, "examples/web/surface-bake.html"), dl: join(root, "examples/web/depth-lab.html") };
for (const [name, where, seconds, setup] of JOBS) {
  const [kind, plate] = where.split(":");
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  const errors = [];
  page.on("pageerror", e => errors.push(String(e)));
  await page.goto(pathToFileURL(pages[kind]).href);
  await page.waitForTimeout(kind === "dl" ? 2500 : 800);
  if (kind === "sb") await page.evaluate(o => window.__sb.setup(o), setup);
  const dir = join(out, `.frames-${name}`); rmSync(dir, { recursive: true, force: true }); mkdirSync(dir);
  const jfps = setup.fps ?? fps, jwidth = setup.width ?? width, colors = setup.colors ?? 160;
  const frames = Math.round(jfps * seconds), dt = 1 / jfps;
  for (let f = 0; f < frames; f++) {
    const url = await page.evaluate(([k, p, t, d]) => (k === "sb" ? window.__sb.frame(d) : window.__dl.render(p, t, d)), [kind, plate, f * dt, dt]);
    writeFileSync(join(dir, String(f).padStart(4, "0") + ".png"), Buffer.from(url.split(",")[1], "base64"));
  }
  const gif = join(out, name + ".gif");
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(jfps), "-i", join(dir, "%04d.png"),
    "-vf", `scale=${jwidth}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=${colors}:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle`,
    "-loop", "0", gif]);
  rmSync(dir, { recursive: true, force: true });
  console.log(`${name}.gif  ${(statSync(gif).size / 1024).toFixed(0)} KB${errors.length ? "  ERRORS: " + errors.join("; ") : ""}`);
  await page.close();
}
await browser.close();
