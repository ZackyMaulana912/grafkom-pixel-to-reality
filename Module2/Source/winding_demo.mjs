/* Module 2 -- pitfall fix (Lab 2 no 4): inconsistent winding.
 * Before: triangleNaive keeps the caller's vertex order, so a triangle given
 * the "wrong" way round has all three edge values <= 0 and draws nothing.
 * After: triangle() swaps two vertices when the total is negative.
 * Measured on Example E4 and on the footprint of my own floor plan, whose
 * vertices are counter-clockwise in metres (y up) and so clockwise on screen.
 *
 *   node winding_demo.mjs
 */
import { Framebuffer, triangle, triangleNaive, edge } from "./raster.mjs";
import { loadPlan, makeWorldToScreen } from "./plan.mjs";

const count = (fn, tris, w, h) => {
  const fb = new Framebuffer(w, h);
  let lit = 0;
  for (const [A, B, C] of tris) lit += fn(fb, A, B, C, [255, 255, 255]);
  return { lit, fb };
};

const E4 = [[1, 1], [6, 2], [3, 7]];
const plan = loadPlan("myplan.json");
const p = plan.silhouette.points.map(makeWorldToScreen(plan, 600));
// fan exactly as the JSON lists the points, without the swap renderPlan does
const fan = [];
for (let i = 1; i + 1 < p.length; i++) fan.push([p[0], p[i], p[i + 1]]);

const rows = [
  ["E4, order A,B,C", [E4], 10, 10],
  ["E4, order A,C,B", [[E4[0], E4[2], E4[1]]], 10, 10],
  ["myplan footprint, JSON order", fan, 800, 600],
];
console.log("case                           total(s)        naive  triangle()");
for (const [label, tris, w, h] of rows) {
  const totals = tris.map(([A, B, C]) => edge(...A, ...B, ...C)).join(", ");
  const n = count(triangleNaive, tris, w, h).lit, t = count(triangle, tris, w, h).lit;
  console.log(`${label.padEnd(31)}${totals.padEnd(16)}${String(n).padStart(6)}  ${String(t).padStart(9)}`);
}
const a = count(triangle, [E4], 10, 10).fb, b = count(triangle, [[E4[0], E4[2], E4[1]]], 10, 10).fb;
console.log(`E4 both orders give byte-identical rasters with triangle(): ${Buffer.compare(Buffer.from(a.data.buffer), Buffer.from(b.data.buffer)) === 0}`);
