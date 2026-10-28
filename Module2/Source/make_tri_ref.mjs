/* Module 2 -- an INDEPENDENT reference for triangle(), because ref/tri_ref.ppm
 * named in the module is not in the starter (and a reference made by the
 * function under test proves nothing).
 *
 * Method, deliberately different from triangle(): every pixel is tested on its
 * own with exact integer arithmetic. Coordinates are doubled, so the sample
 * centre (x + 0.5, y + 0.5) becomes the integer (2x + 1, 2y + 1). The rule is
 * written literally: inside iff each edge value is > 0, or == 0 on a top/left
 * edge. No bias trick, no incremental stepping.
 *
 *   node make_tri_ref.mjs            # (re)write ref/tri_ref.ppm and ref/tri_t8_ref.ppm
 *   node make_tri_ref.mjs --check    # compare raster.mjs triangle() on many triangles
 */
import { mkdirSync } from "node:fs";
import { Framebuffer, triangle } from "./raster.mjs";

const isTopLeft = (X, Y) => {
  const dx = Y[0] - X[0], dy = Y[1] - X[1];
  return (dy === 0 && dx < 0) || dy > 0;
};
const edge2 = (X, Y, px2, py2) =>
  (2 * Y[0] - 2 * X[0]) * (py2 - 2 * X[1]) - (2 * Y[1] - 2 * X[1]) * (px2 - 2 * X[0]);

/** Pixels covered by integer triangle A,B,C (total > 0, y down), as "x,y" keys. */
export function referenceCover(A, B, C, w, h, owns = isTopLeft) {
  for (const V of [A, B, C])
    if (!Number.isInteger(V[0]) || !Number.isInteger(V[1])) throw new Error(`reference needs integer vertices, got ${V}`);
  if (edge2(A, B, 2 * C[0], 2 * C[1]) <= 0) throw new Error("reference needs total > 0");
  const lit = new Set();
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const px2 = 2 * x + 1, py2 = 2 * y + 1;
      const ok = [[B, C], [C, A], [A, B]].every(([X, Y]) => {
        const e = edge2(X, Y, px2, py2);
        return e > 0 || (e === 0 && owns(X, Y));
      });
      if (ok) lit.add(`${x},${y}`);
    }
  return lit;
}

function coverOf(fn, A, B, C, w, h, opts = {}) {
  const lit = new Set();
  fn({ w, h }, A, B, C, null, { ...opts, onFragment: (x, y) => lit.add(`${x},${y}`) });
  return lit;
}

function writeRef(path, A, B, C, w, h) {
  const fb = new Framebuffer(w, h);
  for (const k of referenceCover(A, B, C, w, h)) {
    const [x, y] = k.split(",").map(Number);
    fb.set(x, y, [255, 255, 255]);
  }
  fb.writePPM(path);
  console.log(`wrote ${path}  (${w}x${h}, triangle ${JSON.stringify([A, B, C])})`);
}

// the triangle used throughout the module (Example E4), and the first random
// triangle on which the starter's -1 bias was seen to drop a pixel
export const REFS = [
  { path: "ref/tri_ref.ppm", tri: [[1, 1], [6, 2], [3, 7]], w: 10, h: 10 },
  { path: "ref/tri_t8_ref.ppm", tri: [[16, 0], [4, 23], [2, 12]], w: 32, h: 32 },
];

/** deterministic triangles with integer vertices in [0, 30), all with total > 0 */
export function* sweepTriangles(n = 2000) {
  let seed = 1;
  const rnd = (m) => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % m; };
  for (let t = 0; t < n; t++) {
    let P = [rnd(30), rnd(30)], Q = [rnd(30), rnd(30)], R = [rnd(30), rnd(30)];
    const tot = (Q[0] - P[0]) * (R[1] - P[1]) - (Q[1] - P[1]) * (R[0] - P[0]);
    if (tot === 0) continue;
    if (tot < 0) [Q, R] = [R, Q];
    yield [P, Q, R];
  }
}

/** compare a triangle function against the reference over the sweep */
export function sweep(fn = triangle, { owns = isTopLeft, opts = {} } = {}) {
  let tris = 0, badTris = 0, missing = 0, extra = 0;
  const examples = [];
  for (const [A, B, C] of sweepTriangles()) {
    tris++;
    const ref = referenceCover(A, B, C, 32, 32, owns), got = coverOf(fn, A, B, C, 32, 32, opts);
    const miss = [...ref].filter((k) => !got.has(k)), ext = [...got].filter((k) => !ref.has(k));
    if (miss.length || ext.length) {
      badTris++; missing += miss.length; extra += ext.length;
      if (examples.length < 3) examples.push({ tri: [A, B, C], missing: miss, extra: ext });
    }
  }
  return { tris, badTris, missing, extra, examples };
}

if (process.argv[1] && process.argv[1].endsWith("make_tri_ref.mjs")) {
  if (process.argv.includes("--check")) {
    const r = sweep();
    console.log(`triangle() vs independent reference: ${r.tris} integer triangles in 32x32`);
    console.log(`  triangles that differ: ${r.badTris}   pixels missing: ${r.missing}   pixels extra: ${r.extra}`);
    for (const e of r.examples) console.log(`  e.g. ${JSON.stringify(e.tri)} missing ${e.missing.join(" ")} extra ${e.extra.join(" ")}`);
    mkdirSync("out", { recursive: true });
    for (const { path, tri, w, h } of REFS) {
      const ref = Framebuffer.readPPM(path), fb = new Framebuffer(w, h);
      triangle(fb, ...tri, [255, 255, 255]);
      let diff = 0;
      for (let i = 0; i < fb.data.length; i++) diff = Math.max(diff, Math.abs(fb.data[i] - ref.data[i]));
      console.log(`  ${path}: max |diff| = ${diff}`);
      // grey = both agree, red = only the reference lights it, blue = only triangle() does
      const img = new Framebuffer(w, h);
      for (let y = 0; y < h; y++)
        for (let x = 0; x < w; x++) {
          const r = ref.get(x, y)[0] > 0, g = fb.get(x, y)[0] > 0;
          img.set(x, y, r && g ? [150, 150, 150] : r ? [230, 30, 30] : g ? [30, 90, 230] : [0, 0, 0]);
        }
      const out = path.replace("ref/", "out/").replace("_ref.ppm", "_check.ppm");
      img.writePPM(out);
      console.log(`  wrote ${out} (red = missing in triangle(), blue = extra)`);
    }
  } else {
    mkdirSync("ref", { recursive: true });
    for (const { path, tri, w, h } of REFS) writeRef(path, ...tri, w, h);
  }
}
