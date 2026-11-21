/**
 * Short browser QA for 044 only. Does not render the 191.2s film.
 * Needs production/true3d/node_modules (npm ci) and assets from setup.py.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "../..");
const project = path.join(repo, "episodes/044-water-flosser/true3d");
const require = createRequire(path.join(here, "package.json"));
const puppeteer = require("puppeteer-core");

function chromePath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  for (const candidate of ["/usr/local/bin/google-chrome", "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"]) {
    if (fs.existsSync(candidate)) return candidate;
  }
  throw new Error("未找到 Chrome。设置 CHROME_PATH，或安装 google-chrome / chromium。");
}

function serve(root) {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, "http://127.0.0.1");
    let file = path.join(root, decodeURIComponent(url.pathname));
    if (url.pathname === "/") file = path.join(root, "index.html");
    if (!file.startsWith(root)) {
      res.writeHead(403).end();
      return;
    }
    const types = { ".html": "text/html", ".js": "application/javascript", ".mjs": "text/javascript", ".woff2": "font/woff2", ".wav": "audio/wav" };
    fs.readFile(file, (error, data) => {
      if (error) {
        res.writeHead(404).end();
        return;
      }
      res.setHeader("Content-Type", types[path.extname(file)] || "application/octet-stream");
      res.end(data);
    });
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server)));
}

const server = await serve(project);
const outDir = path.join(project, "artifacts");
fs.mkdirSync(outDir, { recursive: true });
let browser;
try {
  browser = await puppeteer.launch({
    executablePath: chromePath(),
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
  });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto(`http://127.0.0.1:${server.address().port}/?t=8`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => typeof renderFlosserAt === "function");
  const frames = [];
  for (const t of [8, 68, 80]) {
    const result = await page.evaluate((time) => {
      renderFlosserAt(time);
      return window.__3dMeta;
    }, t);
    assert.ok(result.meshCount > 80, `mesh count too low at ${t}`);
    assert.ok(result.triangles > 5000, `triangles too low at ${t}`);
    assert.notEqual(result.pump.inletOpen, result.pump.outletOpen);
    assert.equal(result.pump.rodLength, 0.94);
    frames.push(result);
    await page.screenshot({ path: path.join(outDir, `qa-${t}s.png`) });
  }
  const kinematics = await page.evaluate(() => {
    for (let i = 0; i < 360; i += 1) {
      const state = pumpStateForQA((i / 360) * Math.PI * 2);
      const len = Math.hypot(state.slider - state.pin.x, state.pin.y);
      if (Math.abs(len - 0.94) > 1e-9 || state.inletOpen === state.outletOpen) return false;
    }
    return true;
  });
  assert.equal(kinematics, true);
  const deterministic = await page.evaluate(() => {
    renderFlosserAt(90);
    const first = document.querySelector("canvas").toDataURL();
    renderFlosserAt(157);
    renderFlosserAt(1);
    renderFlosserAt(90);
    return first === document.querySelector("canvas").toDataURL();
  });
  assert.equal(deterministic, true);
  assert.deepEqual(errors, []);
  const summary = { kinematics, deterministic, errors, frames: frames.map(({ time, meshCount, triangles, pump }) => ({ time, meshCount, triangles, pump })) };
  fs.writeFileSync(path.join(outDir, "qa-summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
} finally {
  if (browser) await browser.close();
  server.close();
}
