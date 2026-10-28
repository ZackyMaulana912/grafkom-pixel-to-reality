/* Module 2 -- which edge owns a pixel that sits exactly on it: the module's
 * rule or the GPU's? ref/gpu_e4.ppm and ref/gpu_square.ppm were captured from
 * web/gpu_rule.html (raw WebGL2, no antialiasing) in Chrome 156 on an Apple M5
 * (ANGLE Metal) and, byte-identical, on ANGLE SwiftShader.
 *
 *   node gpu_rule_check.mjs
 */
import { Framebuffer, triangle } from "./raster.mjs";
import { pixelStats } from "./metrics.mjs";
import { sweep } from "./make_tri_ref.mjs";

// the GPU's tie rule written out literally, for the independent reference
const gpuOwns = (X, Y) => { const dx = Y[0] - X[0], dy = Y[1] - X[1]; return (dy === 0 && dx > 0) || dy < 0; };

export const GPU_REFS = [
  { path: "ref/gpu_e4.ppm", tris: [[[1, 1], [6, 2], [3, 7], [255, 255, 255]]] },
  { path: "ref/gpu_square.ppm", tris: [[[2, 2], [8, 2], [8, 8], [230, 120, 40]], [[2, 2], [8, 8], [2, 8], [40, 130, 180]]] },
];

/** draw a GPU_REFS entry with one fill rule; returns the framebuffer */
export function drawRef({ tris }, fillRule) {
  const fb = new Framebuffer(12, 12);
  for (const [A, B, C, rgb] of tris) triangle(fb, A, B, C, rgb, { fillRule });
  return fb;
}

export const gpuSweep = () => sweep(triangle, { owns: gpuOwns, opts: { fillRule: "gpu" } });

if (process.argv[1] && process.argv[1].endsWith("gpu_rule_check.mjs")) {
  for (const ref of GPU_REFS) {
    const gpu = Framebuffer.readPPM(ref.path);
    for (const rule of ["module", "gpu"]) {
      const fb = drawRef(ref, rule), st = pixelStats(fb, gpu);
      const diff = [];
      for (let y = 0; y < 12; y++)
        for (let x = 0; x < 12; x++) if (fb.get(x, y).join() !== gpu.get(x, y).join()) diff.push(`(${x},${y})`);
      console.log(`${ref.path} vs triangle(fillRule "${rule}"): ${st.identical}/${st.total} identical, ` +
        `max|diff| ${st.maxAbs}${diff.length ? `, differ at ${diff.join(" ")}` : ""}`);
    }
  }
  const r = gpuSweep();
  console.log(`fillRule "gpu" vs independent reference with the GPU tie rule: ${r.badTris}/${r.tris} triangles differ, ` +
    `${r.missing} missing, ${r.extra} extra`);
}
