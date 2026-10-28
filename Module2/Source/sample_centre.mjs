/* Module 2 -- sample-centre check (Lab 2 no 3, Example E1): fill a 2x2
 * rectangle at (1,1) by testing pixel centres, pixel corners, and pixel
 * corners with an inclusive bound, then once more with the rectangle moved by
 * a quarter pixel so the corner test's half-pixel shift becomes visible.
 *
 *   node sample_centre.mjs
 */
import { mkdirSync } from "node:fs";
import { Framebuffer, fillRect } from "./raster.mjs";

mkdirSync("out", { recursive: true });
const show = (pts) => pts.map((p) => `(${p})`).join(" ");
const cases = [
  ["integer rect [1,3) x [1,3)", [1, 1, 3, 3]],
  ["moved rect [1.25,3.25) x [1.25,3.25)", [1.25, 1.25, 3.25, 3.25]],
];
for (const [label, r] of cases) {
  console.log(`== ${label} ==`);
  for (const sample of ["centre", "corner", "corner-inclusive"]) {
    const fb = new Framebuffer(6, 6);
    const lit = fillRect(fb, ...r, [255, 255, 255], { sample });
    console.log(`  ${sample.padEnd(17)} ${String(lit.length).padStart(2)} px  ${show(lit)}`);
    if (r[0] === 1) fb.writePPM(`out/rect_${sample}.ppm`);
  }
}
console.log("wrote out/rect_{centre,corner,corner-inclusive}.ppm (integer rect)");
