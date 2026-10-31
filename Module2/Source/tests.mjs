/* Module 2 -- run every from-scratch check. `npm test` / `node tests.mjs`.
 * Exit 0 iff all pass. Covers the hand-checkable invariants of Examples
 * E1-E5, watertightness (top-left rule), and the reference raster match. */
import {
  Framebuffer, lineDDA, lineBresenham, edge, triangle, triangleNaive, barycentric, coverage, fillRect,
} from "./raster.mjs";
import { makeWorldToScreen, loadPlan, renderPlan, newFramebufferForPlan, legendOf } from "./plan.mjs";
import { pixelStats } from "./metrics.mjs";
import { asterisk } from "./draw_asterisk.mjs";
import { sweep, REFS } from "./make_tri_ref.mjs";
import { encodePNG } from "./export_png.mjs";
import { views, minPair, BAD, MACHADO_2009, machadoViews } from "./cvd_check.mjs";
import { GPU_REFS, drawRef, gpuSweep } from "./gpu_rule_check.mjs";
import { existsSync, mkdirSync } from "node:fs";
import { inflateSync } from "node:zlib";

let pass = 0, fail = 0;
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
function check(name, fn) {
  try { fn(); console.log("OK   " + name); pass++; }
  catch (e) { console.log("FAIL " + name + "\n     " + e.message); fail++; }
}
const assert = (c, m) => { if (!c) throw new Error(m || "assertion failed"); };

const RUNLINE = [[2, 1], [3, 2], [4, 2], [5, 3], [6, 3], [7, 4], [8, 4], [9, 5]];

check("E2 -- lineDDA (2,1)->(9,5) gives the 8-pixel staircase", () => {
  assert(eq(lineDDA(2, 1, 9, 5), RUNLINE), "DDA pixel list mismatch");
});

check("E3 -- lineBresenham (2,1)->(9,5) matches DDA, integers only", () => {
  assert(eq(lineBresenham(2, 1, 9, 5), RUNLINE), "Bresenham pixel list mismatch");
});

check("lines -- all 8 octants: the reflected segment has the same length", () => {
  const base = lineBresenham(0, 0, 9, 4).length; // 10
  for (const [sx, sy] of [[1, 1], [-1, 1], [1, -1], [-1, -1]])
    for (const [a, b] of [[9, 4], [4, 9]]) {
      const n = lineBresenham(0, 0, sx * a, sy * b).length;
      assert(n === Math.max(a, b) + 1, `octant ${sx},${sy},${a},${b}: ${n}`);
    }
  assert(base === 10, "baseline length");
});

check("E4 -- edge-function signs for A(1,1) B(6,2) C(3,7)", () => {
  const A = [1, 1], B = [6, 2], C = [3, 7];
  const total = edge(A[0], A[1], B[0], B[1], C[0], C[1]);
  assert(total === 28, `total ${total} != 28`);
  const E = (P) => [
    edge(A[0], A[1], B[0], B[1], P[0], P[1]),
    edge(B[0], B[1], C[0], C[1], P[0], P[1]),
    edge(C[0], C[1], A[0], A[1], P[0], P[1]),
  ];
  assert(eq(E([3, 3]), [8, 12, 8]), "P1 (3,3) edge values");
  assert(E([5, 5]).some((v) => v < 0), "P2 (5,5) should be outside");
  assert(E([1, 4]).some((v) => v < 0), "P3 (1,4) should be outside");
  assert(E([3, 3]).every((v) => v >= 0), "P1 (3,3) should be inside");
});

check("E5 -- barycentric interpolation 10/20/40 at (.5,.25,.25) = 20", () => {
  const A = [0, 0], B = [4, 0], C = [0, 4];
  // point with barycentric (0.5, 0.25, 0.25): P = .5A + .25B + .25C = (1,1)
  const [la, lb, lc] = barycentric(A, B, C, [1, 1]);
  assert(Math.abs(la + lb + lc - 1) < 1e-12, "weights sum to 1");
  assert(Math.abs(la - 0.5) < 1e-12 && Math.abs(lb - 0.25) < 1e-12 && Math.abs(lc - 0.25) < 1e-12,
    `weights ${la},${lb},${lc}`);
  const v = la * 10 + lb * 20 + lc * 40;
  assert(Math.abs(v - 20) < 1e-12, `interp ${v} != 20`);
});

check("top-left rule -- 6x6 square split on y=x: every pixel covered once", () => {
  const T1 = [[2, 2], [8, 2], [8, 8]], T2 = [[2, 2], [8, 8], [2, 8]];
  const c = coverage(12, 12, [T1, T2], { topLeft: true });
  assert(c.once === 36 && c.twice === 0 && c.gaps === 0,
    `once=${c.once} twice=${c.twice} gaps=${c.gaps}`);
});

check("no top-left rule -- same square shows the seam (>=0: doubles; >0: gaps)", () => {
  const T1 = [[2, 2], [8, 2], [8, 8]], T2 = [[2, 2], [8, 8], [2, 8]];
  const dbl = coverage(12, 12, [T1, T2], { topLeft: false });
  const crk = coverage(12, 12, [T1, T2], { topLeft: false, strictGreater: true });
  assert(dbl.twice === 6 && dbl.gaps === 0, `>=0: twice=${dbl.twice} gaps=${dbl.gaps}`);
  assert(crk.twice === 0 && crk.gaps === 6, `>0: twice=${crk.twice} gaps=${crk.gaps}`);
});

check("E1 -- sample-centre: a 2x2 rect at (1,1) lights exactly (1,1),(2,1),(1,2),(2,2)", () => {
  const fb = new Framebuffer(6, 6);
  // fill x in [1,3), y in [1,3) by centre rule
  const lit = [];
  for (let y = 0; y < 6; y++)
    for (let x = 0; x < 6; x++) {
      const cx = x + 0.5, cy = y + 0.5;
      if (cx >= 1 && cx < 3 && cy >= 1 && cy < 3) { fb.set(x, y, [255, 255, 255]); lit.push([x, y]); }
    }
  assert(eq(lit, [[1, 1], [2, 1], [1, 2], [2, 2]]), `lit ${JSON.stringify(lit)}`);
});

check("plan -- worldToScreen flips y once and is invertible on a known point", () => {
  const plan = loadPlan("pusaka_plan.json");
  const H = 600;
  const w2s = makeWorldToScreen(plan, H);
  const s = plan.scale_px_per_m, [ox, oy] = plan.origin_m;
  const p = w2s([0, 0]);
  assert(p[0] === Math.round(ox * s), `x ${p[0]}`);
  assert(p[1] === Math.round(H - 1 - oy * s), `y ${p[1]}`);
  // moving +y in world moves UP on screen (smaller y)
  assert(w2s([0, 5])[1] < w2s([0, 0])[1], "y not flipped");
});

check("reference raster -- draw_square fill is byte-identical to ref/square_fill_ref.ppm", () => {
  if (!existsSync("ref/square_fill_ref.ppm")) {
    console.log("     (ref missing -- generating it now; commit ref/ after first run)");
    mkdirSync("ref", { recursive: true });
    const g = new Framebuffer(12, 12);
    triangle(g, [2, 2], [8, 2], [8, 8], [230, 120, 40]);
    triangle(g, [2, 2], [8, 8], [2, 8], [40, 130, 180]);
    g.writePPM("ref/square_fill_ref.ppm");
  }
  const fb = new Framebuffer(12, 12);
  triangle(fb, [2, 2], [8, 2], [8, 8], [230, 120, 40]);
  triangle(fb, [2, 2], [8, 8], [2, 8], [40, 130, 180]);
  const ref = Framebuffer.readPPM("ref/square_fill_ref.ppm");
  const st = pixelStats(fb, ref);
  assert(st.identical === st.total && st.maxAbs === 0,
    `identical ${st.identical}/${st.total}, max|diff| ${st.maxAbs}`);
});

// ------------------------------------------------------- added in this repo

check("lines -- 8 reflections of (0,0)->(9,4): start, end, 8-connected, within 0.5 px", () => {
  for (const [sx, sy] of [[1, 1], [-1, 1], [1, -1], [-1, -1]])
    for (const [a, b] of [[9, 4], [4, 9]]) {
      const ex = sx * a, ey = sy * b, pts = lineBresenham(0, 0, ex, ey);
      const last = pts[pts.length - 1];
      assert(eq(pts[0], [0, 0]) && eq(last, [ex, ey]), `octant ${ex},${ey}: ends ${pts[0]} ${last}`);
      for (let k = 1; k < pts.length; k++)
        assert(Math.max(Math.abs(pts[k][0] - pts[k - 1][0]), Math.abs(pts[k][1] - pts[k - 1][1])) === 1,
          `octant ${ex},${ey}: gap or repeat at step ${k}`);
      const xMajor = Math.abs(ex) >= Math.abs(ey);
      for (const [x, y] of pts) {
        const off = xMajor ? Math.abs(y - (ey * x) / ex) : Math.abs(x - (ex * y) / ey);
        assert(off <= 0.5 + 1e-12, `octant ${ex},${ey}: (${x},${y}) is ${off} px off the line`);
      }
    }
});

check("asterisk -- 24 spokes every 15 deg reach R +/- 1 px and stay within 0.5 px of their line", () => {
  const spokes = asterisk(120, 120, 110);
  assert(spokes.length === 24, "spoke count");
  for (const s of spokes) {
    assert(Math.abs(s.reach - 110) <= 1, `${s.deg} deg reaches ${s.reach}`);
    assert(s.wander <= 0.5 + 1e-12, `${s.deg} deg wanders ${s.wander}`);
    assert(s.pixels === s.expected, `${s.deg} deg: ${s.pixels} px, expected ${s.expected}`);
  }
});

check("E1b -- corner test with an inclusive bound lights a 3x3 block, centre rule 2x2", () => {
  const centre = fillRect(null, 1, 1, 3, 3, undefined, { sample: "centre" });
  const corner = fillRect(null, 1, 1, 3, 3, undefined, { sample: "corner-inclusive" });
  assert(eq(centre, [[1, 1], [2, 1], [1, 2], [2, 2]]), `centre ${JSON.stringify(centre)}`);
  const want = [];
  for (let y = 1; y <= 3; y++) for (let x = 1; x <= 3; x++) want.push([x, y]);
  assert(eq(corner, want), `corner-inclusive ${JSON.stringify(corner)}`);
  // a quarter-pixel move shows the corner test's shift: centre keeps (1..2), corner moves to (2..3)
  const moved = fillRect(null, 1.25, 1.25, 3.25, 3.25, undefined, { sample: "corner" });
  assert(eq(moved, [[2, 2], [3, 2], [2, 3], [3, 3]]), `moved corner ${JSON.stringify(moved)}`);
});

check("E4 -- barycentric of P1 (3,3) is (3/7, 2/7, 2/7); triangleNaive fills the same 6x6 seam", () => {
  const [a, b, c] = barycentric([1, 1], [6, 2], [3, 7], [3, 3]);
  assert(Math.abs(a - 3 / 7) < 1e-12 && Math.abs(b - 2 / 7) < 1e-12 && Math.abs(c - 2 / 7) < 1e-12, `${a},${b},${c}`);
  const counts = new Int32Array(144);
  for (const T of [[[2, 2], [8, 2], [8, 8]], [[2, 2], [8, 8], [2, 8]]])
    triangleNaive({ w: 12, h: 12 }, ...T, null, { onFragment: (x, y) => counts[y * 12 + x]++ });
  const twice = [...counts].filter((k) => k >= 2).length;
  assert(twice === 6, `triangleNaive doubles ${twice}`);
});

check("top-left on fixed point -- triangle() equals the independent reference on 1934 triangles", () => {
  const r = sweep(triangle);
  assert(r.badTris === 0 && r.missing === 0 && r.extra === 0,
    `${r.badTris} triangles differ, ${r.missing} missing, ${r.extra} extra, e.g. ${JSON.stringify(r.examples[0])}`);
});

check("reference raster -- triangle() matches ref/tri_ref.ppm and ref/tri_t8_ref.ppm, max|diff| = 0", () => {
  for (const { path, tri, w, h } of REFS) {
    const fb = new Framebuffer(w, h);
    triangle(fb, ...tri, [255, 255, 255]);
    const st = pixelStats(fb, Framebuffer.readPPM(path));
    assert(st.identical === st.total && st.maxAbs === 0, `${path}: ${st.identical}/${st.total}, max|diff| ${st.maxAbs}`);
  }
});

check("fill rule \"gpu\" -- matches the pixels WebGL drew (ref/gpu_*.ppm) and its own reference; still watertight", () => {
  for (const ref of GPU_REFS) {
    const st = pixelStats(drawRef(ref, "gpu"), Framebuffer.readPPM(ref.path));
    assert(st.identical === st.total && st.maxAbs === 0, `${ref.path}: ${st.identical}/${st.total}`);
  }
  const r = gpuSweep();
  assert(r.badTris === 0, `${r.badTris} triangles differ from the GPU-rule reference`);
  const c = coverage(12, 12, [[[2, 2], [8, 2], [8, 8]], [[2, 2], [8, 8], [2, 8]]], { fillRule: "gpu" });
  assert(c.once === 36 && c.twice === 0 && c.gaps === 0, `once=${c.once} twice=${c.twice} gaps=${c.gaps}`);
});

check("winding -- a reversed triangle fills the same pixels; triangleNaive drops it", () => {
  const A = [1, 1], B = [6, 2], C = [3, 7];
  const f = new Framebuffer(10, 10), r = new Framebuffer(10, 10), n = new Framebuffer(10, 10);
  const lit = triangle(f, A, B, C), litRev = triangle(r, A, C, B);
  assert(lit === 14 && litRev === 14, `lit ${lit} / ${litRev}`);
  assert(pixelStats(f, r).maxAbs === 0, "reversed order changed the raster");
  assert(triangleNaive(n, A, C, B) === 0, "triangleNaive should draw nothing for the reversed order");
});

check("myplan -- every point inside 800x600, 5 legend categories, every category in the legend", () => {
  const plan = loadPlan("myplan.json"), w2s = makeWorldToScreen(plan, 600);
  for (const pl of [...plan.polylines, plan.silhouette])
    for (const p of pl.points) {
      const [x, y] = w2s(p);
      assert(x >= 0 && y >= 0 && x < 800 && y < 600, `${pl.id} point ${p} -> (${x},${y}) is off-canvas`);
    }
  const cats = legendOf(plan).map((e) => e.category);
  assert(cats.length === 5 && new Set(cats).size === 5, `legend ${cats}`);
  for (const pl of plan.polylines) assert(cats.includes(pl.category), `${pl.id}: category ${pl.category} not in legend`);
});

check("myplan -- footprint fills exactly 260 x 520 px, each pixel once, no zero-area triangle", () => {
  const plan = loadPlan("myplan.json"), p = plan.silhouette.points.map(makeWorldToScreen(plan, 600));
  const tris = [];
  for (let i = 1; i + 1 < p.length; i++) tris.push([p[0], p[i], p[i + 1]]);
  for (const [A, B, C] of tris) assert(edge(...A, ...B, ...C) !== 0, "zero-area fan triangle");
  const cov = coverage(800, 600, tris, { topLeft: true });
  assert(cov.once === 260 * 520 && cov.twice === 0 && cov.gaps === 0, `once=${cov.once} twice=${cov.twice} gaps=${cov.gaps}`);
  const fb = newFramebufferForPlan(plan, 800, 600);
  renderPlan(fb, plan, { fillSilhouette: true });
  assert(eq(fb.get(400, 300), [230, 236, 245]), "floor colour at the room centre");
});

check("legend -- all 5 categories stay >= 20 apart under the page's CVD filters; red/green fails", () => {
  const V = views(), labels = legendOf(loadPlan("myplan.json")).map((e) => e.label);
  const cols = legendOf(loadPlan("myplan.json")).map((e) => e.rgb);
  for (const [name, f] of Object.entries(V)) {
    const m = minPair(cols.map(f), labels);
    assert(m.d >= 20, `${name}: ${m.pair} only ${m.d.toFixed(1)} apart`);
  }
  assert(minPair(BAD.map(V.deuteranopia), BAD.map(String)).d < 20, "the red/green control should collapse");
});

check("legend -- Machado et al. 2009 (published model) gives the same verdict as the page's matrices", () => {
  const legend = legendOf(loadPlan("myplan.json"));
  const labels = legend.map((e) => e.label), cols = legend.map((e) => e.rgb);
  for (const [kind, M] of Object.entries(MACHADO_2009))
    for (const row of M) assert(Math.abs(row[0] + row[1] + row[2] - 1) < 2e-6, `${kind}: white must stay white`);
  for (const [name, f] of Object.entries(machadoViews())) {
    const m = minPair(cols.map(f), labels);
    assert(m.d >= 20, `Machado ${name}: ${m.pair} only ${m.d.toFixed(1)} apart`);
    assert(minPair(BAD.map(f), BAD.map(String)).d < 20, `Machado ${name}: the red/green control should collapse`);
  }
});

check("export_png -- the PNG encoder round-trips a raster through node:zlib", () => {
  const fb = new Framebuffer(5, 3);
  for (let i = 0; i < fb.data.length; i++) fb.data[i] = (i * 37) % 256;
  const png = encodePNG(fb);
  assert(png.subarray(1, 4).toString("ascii") === "PNG", "signature");
  const idatLen = png.readUInt32BE(33), raw = inflateSync(png.subarray(41, 41 + idatLen));
  for (let y = 0; y < 3; y++) {
    assert(raw[y * 16] === 0, "filter byte");
    assert(Buffer.compare(raw.subarray(y * 16 + 1, y * 16 + 16), Buffer.from(fb.data.subarray(y * 15, y * 15 + 15))) === 0, `row ${y}`);
  }
});

console.log(`\n${fail === 0 ? "ALL CHECKS PASSED" : fail + " CHECK(S) FAILED"}  (${pass} ok, ${fail} fail)`);
process.exit(fail === 0 ? 0 : 1);
