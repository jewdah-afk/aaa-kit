// Loads every HTML page under examples/ and tools/ in headless Chromium, runs it for 1.5 s
// at phone and desktop sizes, taps the middle of the first canvas, and fails on any console
// error, page error or failed request. Usage: node tools/check_examples.mjs [--shots dir]
import { readdirSync, statSync, mkdirSync } from "node:fs";
import { join, resolve, relative } from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); }
catch { ({ chromium } = await import("playwright")); }

const root = resolve(new URL("..", import.meta.url).pathname);
const shotsArg = process.argv.indexOf("--shots");
const shots = shotsArg > 0 ? resolve(process.argv[shotsArg + 1]) : null;
if (shots) mkdirSync(shots, { recursive: true });

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name.startsWith(".git")) continue;
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (name.endsWith(".html") && !name.endsWith(".tpl.html")) out.push(p);
  }
  return out;
}

const pages = [...walk(join(root, "examples")), ...walk(join(root, "tools"))];
const browser = await chromium.launch();
let failed = 0;
for (const file of pages) {
  for (const vp of [{ width: 390, height: 844, name: "phone" }, { width: 1280, height: 800, name: "desktop" }]) {
    const page = await browser.newPage({ viewport: vp, deviceScaleFactor: 1 });
    const errors = [];
    page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
    page.on("pageerror", e => errors.push(String(e)));
    page.on("requestfailed", r => { if (!r.url().startsWith("https://fonts.")) errors.push("request failed: " + r.url()); });
    await page.goto(pathToFileURL(file).href + "?all");
    await page.waitForTimeout(800);
    const c = await page.$("canvas");
    if (c) { const b = await c.boundingBox(); if (b) await page.mouse.click(b.x + b.width / 2, b.y + b.height / 2); }
    await page.waitForTimeout(700);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
    if (overflow) errors.push("horizontal scroll at " + vp.name);
    if (shots) await page.screenshot({ path: join(shots, relative(root, file).replace(/[\\/]/g, "_") + "." + vp.name + ".png") });
    const rel = relative(root, file);
    if (errors.length) { failed++; console.log("FAIL", rel, vp.name, "\n  " + errors.slice(0, 5).join("\n  ")); }
    else console.log("ok  ", rel, vp.name);
    await page.close();
  }
}
await browser.close();
console.log(`${pages.length} pages, ${failed} failures`);
process.exit(failed ? 1 : 0);
