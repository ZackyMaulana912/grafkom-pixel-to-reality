/* Module 2 -- is the legend still readable under the page's own CVD filters?
 * (Lab 3 no 4, A5). The deuteranopia / protanopia matrices are READ FROM
 * web/index.html, so this checks exactly what the page applies. SVG
 * feColorMatrix works in linearRGB unless color-interpolation-filters says
 * otherwise, and cvd.css does not, so the matrix is applied to linear light,
 * as Module 1's cvd.py does with the same numbers.
 *
 * The page's grayscale toggle is CSS grayscale(1); in Chrome it weights the
 * sRGB CODES (0.2126, 0.7152, 0.0722), checked against screenshots, so it is
 * modelled that way here, next to Module 1's linear-light grey.
 *
 * Distance = Euclidean distance between two simulated colours in sRGB codes,
 * the measure and the threshold (20) of Module 1's legend guard.
 *
 *   node cvd_check.mjs [--plan myplan.json]
 */
import { readFileSync } from "node:fs";
import { loadPlan, legendOf } from "./plan.mjs";

const THRESH = 20;
const dec = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
const enc = (v) => {
  v = Math.min(1, Math.max(0, v));
  return Math.round(255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055));
};

/** the 3x3 part of each <feColorMatrix> in web/index.html, by filter id */
export function pageMatrices(path = "web/index.html") {
  const html = readFileSync(path, "utf8"), out = {};
  for (const m of html.matchAll(/<filter id="(\w+)">\s*<feColorMatrix type="matrix" values="([^"]+)"/g)) {
    const v = m[2].trim().split(/\s+/).map(Number);
    out[m[1]] = [[v[0], v[1], v[2]], [v[5], v[6], v[7]], [v[10], v[11], v[12]]];
  }
  return out;
}

const inLinear = (M) => (rgb) => {
  const l = rgb.map(dec);
  return M.map((r) => enc(r[0] * l[0] + r[1] * l[1] + r[2] * l[2]));
};
const onCodes = (M) => (rgb) => M.map((r) => Math.min(255, Math.max(0, Math.round(r[0] * rgb[0] + r[1] * rgb[1] + r[2] * rgb[2]))));
const grey = (rgb) => { const l = rgb.map(dec), y = enc(0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2]); return [y, y, y]; };
const cssGrey = (rgb) => { const y = Math.round(0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]); return [y, y, y]; };
const luminance = (rgb) => { const l = rgb.map(dec); return 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2]; };

/** smallest pairwise distance and the pair it occurs at */
export function minPair(cols, labels) {
  let best = { d: Infinity };
  for (let i = 0; i < cols.length; i++)
    for (let j = i + 1; j < cols.length; j++) {
      const d = Math.hypot(...cols[i].map((v, k) => v - cols[j][k]));
      if (d < best.d) best = { d, pair: `${labels[i]} / ${labels[j]}` };
    }
  return best;
}

export function views() {
  const M = pageMatrices();
  return {
    normal: (c) => c,
    deuteranopia: inLinear(M.deuteranopia),
    protanopia: inLinear(M.protanopia),
    grayscale: grey,
    "grayscale-css": cssGrey,
  };
}

// a hue-only red/green palette, the kind Module 1 rejects; it must FAIL here
export const BAD = [[200, 40, 40], [40, 170, 40], [210, 150, 30], [150, 90, 40], [90, 160, 40]];

if (process.argv[1] && process.argv[1].endsWith("cvd_check.mjs")) {
  const pi = process.argv.indexOf("--plan");
  const legend = legendOf(loadPlan(pi >= 0 ? process.argv[pi + 1] : "myplan.json"));
  const labels = legend.map((e) => e.label), cols = legend.map((e) => e.rgb);
  const V = views(), M = pageMatrices();
  console.log("legend: " + legend.map((e) => `${e.label} rgb(${e.rgb}) Y=${luminance(e.rgb).toFixed(3)}`).join(", "));
  let ok = true;
  for (const [name, f] of Object.entries(V)) {
    const sim = cols.map(f), m = minPair(sim, labels);
    ok &&= m.d >= THRESH;
    console.log(`${name.padEnd(13)} min distance ${m.d.toFixed(1).padStart(6)} (${m.pair})   ` +
      sim.map((c) => `(${c})`).join(" "));
  }
  const codes = minPair(cols.map(onCodes(M.deuteranopia)), labels);
  console.log(`for comparison, the same deuteranopia matrix on sRGB codes: min distance ${codes.d.toFixed(1)} (${codes.pair})`);
  const bad = Object.fromEntries(Object.entries(V).map(([n, f]) => [n, minPair(BAD.map(f), BAD.map(String)).d.toFixed(1)]));
  console.log(`negative control, red/green palette: ${JSON.stringify(bad)}`);
  console.log(ok ? `legend distinct in every view (>= ${THRESH})` : "LEGEND COLLAPSES in at least one view");
  process.exit(ok ? 0 : 1);
}
