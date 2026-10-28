/* Module 2 -- DIAGNOSE-AND-FIX: shared-edge cracks / double-draws.
 *
 * The bug artifact: a quad drawn as two triangles WITHOUT the top-left rule.
 * Your Lab 2 task -- from the rendered pixels only, before reading the fix:
 *   1. show which pixels are covered twice (or missing) and count them;
 *   2. state the cause;
 *   3. switch to the top-left rule;
 *   4. prove 0 doubles and 0 gaps.
 *
 *   node triangle_gap_bug.mjs --diagnose   # pixel evidence only, no cause, no fix
 *   node triangle_gap_bug.mjs              # runs all three modes, prints evidence
 */
import { Framebuffer, triangle, coverage } from "./raster.mjs";
import { mkdirSync } from "node:fs";

mkdirSync("out", { recursive: true });

// same 6x6 square + diagonal as the Fully Worked Example
const T1 = [[2, 2], [8, 2], [8, 8]];
const T2 = [[2, 2], [8, 8], [2, 8]];
const W = 12, H = 12;

function run(label, opts) {
  const fb = new Framebuffer(W, H);
  triangle(fb, T1[0], T1[1], T1[2], [230, 120, 40], opts);
  triangle(fb, T2[0], T2[1], T2[2], [40, 130, 180], opts);
  const cov = coverage(W, H, [T1, T2], opts);
  console.log(
    `${label.padEnd(26)} once=${cov.once}  twice=${cov.twice}  gaps=${cov.gaps}`
  );
  return { fb, cov };
}

/** coverage image: red = covered twice, grey = once, white = gap, black = outside */
function coverageImage(cov, path) {
  const union = coverage(W, H, [T1, T2], { topLeft: false }).counts;
  const img = new Framebuffer(W, H);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const c = cov.counts[y * W + x];
      img.set(x, y, c >= 2 ? [220, 30, 30] : c === 1 ? [120, 120, 120]
        : union[y * W + x] ? [255, 255, 255] : [0, 0, 0]);
    }
  img.writePPM(path);
}

/** pixel evidence for one fill rule: counts, coordinates, an ASCII map */
function evidence(label, opts, path) {
  const { cov } = run(label, opts);
  const union = coverage(W, H, [T1, T2], { topLeft: false }).counts;
  const twice = [], gaps = [];
  let map = "";
  for (let y = 0; y < H; y++) {
    let row = "";
    for (let x = 0; x < W; x++) {
      const c = cov.counts[y * W + x];
      if (c >= 2) twice.push(`(${x},${y})`);
      if (c === 0 && union[y * W + x]) gaps.push(`(${x},${y})`);
      row += c >= 2 ? "2" : c === 1 ? "1" : union[y * W + x] ? "_" : ".";
    }
    map += `    ${row}\n`;
  }
  console.log(`  covered twice: ${twice.length ? twice.join(" ") : "none"}`);
  console.log(`  gaps         : ${gaps.length ? gaps.join(" ") : "none"}`);
  console.log(`  map (2 = twice, 1 = once, _ = gap, . = outside):\n${map}`);
  coverageImage(cov, path);
  console.log(`  wrote ${path}\n`);
}

if (process.argv.includes("--diagnose")) {
  console.log("== evidence only: two triangles tiling a 6x6 quad, no fill rule ==\n");
  evidence("inside if all E >= 0", { topLeft: false }, "out/gap_coverage_buggy.ppm");
  evidence("inside if all E > 0", { topLeft: false, strictGreater: true }, "out/gap_coverage_strict.ppm");
  process.exit(0);
}

console.log("== evidence: two triangles tiling a 6x6 quad along y = x ==");
const buggy = run("naive >=0 (no rule)", { topLeft: false });
const cracks = run("strict >0 (no rule)", { topLeft: false, strictGreater: true });
const fixed = run("top-left rule", { topLeft: true });

coverageImage(buggy.cov, "out/gap_coverage_buggy.ppm");
coverageImage(cracks.cov, "out/gap_coverage_strict.ppm");
coverageImage(fixed.cov, "out/gap_coverage_fixed.ppm");
fixed.fb.writePPM("out/gap_fixed.ppm");

console.log("\nroot cause : pixels whose centre lies exactly on the shared edge");
console.log("             have an edge function == 0 in BOTH triangles.");
console.log("the fix    : per-edge top-left bias -- 0 for a top/left edge,");
console.log("             -1 otherwise -- so each on-edge pixel is claimed once.");
console.log(`proof      : top-left rule -> twice=${fixed.cov.twice}, gaps=${fixed.cov.gaps}`);
console.log("wrote out/gap_coverage_{buggy,strict,fixed}.ppm (red = double, white = gap), out/gap_fixed.ppm");
if (!(fixed.cov.twice === 0 && fixed.cov.gaps === 0))
  throw new Error("top-left rule did not produce a watertight fill");
