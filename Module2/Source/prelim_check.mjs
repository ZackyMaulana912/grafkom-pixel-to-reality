/* Module 2 -- recompute every number used in the Studi Pendahuluan (Q2-Q4).
 *
 * Each value printed here is the one written in
 * ../docs/studi-pendahuluan/studi-pendahuluan.md, and each is asserted, so the
 * script exits non-zero if the write-up and the arithmetic ever disagree.
 *
 *   node prelim_check.mjs
 */
import { lineDDA, lineBresenham, edge, barycentric, coverage } from "./raster.mjs";

const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
function assert(c, m) { if (!c) throw new Error(m); }
const close = (a, b, tol = 1e-12) => assert(Math.abs(a - b) <= tol, `${a} != ${b}`);

function q2() {
  console.log("== Q2(a): DDA (2,1) -> (9,5) ==");
  const [x0, y0, x1, y1] = [2, 1, 9, 5];
  const dx = x1 - x0, dy = y1 - y0, steps = Math.max(Math.abs(dx), Math.abs(dy));
  assert(dx === 7 && dy === 4 && steps === 7, "deltas");
  console.log(`  dx=${dx} dy=${dy} steps=${steps} x_inc=${dx / steps} y_inc=${(dy / steps).toFixed(4)}`);
  const yk = [];
  for (let k = 0; k <= steps; k++) yk.push(+(y0 + (k * dy) / steps).toFixed(3));
  assert(eq(yk, [1, 1.571, 2.143, 2.714, 3.286, 3.857, 4.429, 5]), `y_k ${yk}`);
  console.log(`  y_k = ${yk.map((v) => v.toFixed(3)).join(", ")}`);
  const PIX = [[2, 1], [3, 2], [4, 2], [5, 3], [6, 3], [7, 4], [8, 4], [9, 5]];
  assert(eq(lineDDA(x0, y0, x1, y1), PIX), "lineDDA pixels");
  console.log(`  pixels = ${PIX.map((p) => `(${p})`).join(" ")}  (${PIX.length} pixel)`);

  console.log("== Q2(b): Bresenham, same segment ==");
  // independent trace of the decision variable, not the raster.mjs loop
  let D = 2 * dy - dx, y = y0;
  const trace = [D], pix = [];
  for (let x = x0; x <= x1; x++) {
    pix.push([x, y]);
    if (x === x1) break;
    if (D > 0) { y += 1; D += 2 * (dy - dx); } else D += 2 * dy;
    trace.push(D);
  }
  assert(eq(trace, [1, -5, 3, -3, 5, -1, 7, 1]), `D trace ${trace}`);
  assert(eq(pix, PIX) && eq(lineBresenham(x0, y0, x1, y1), PIX), "Bresenham pixels");
  console.log(`  2dy=${2 * dy}  2(dy-dx)=${2 * (dy - dx)}  D = ${trace.join(", ")}`);
}

function q3() {
  console.log("== Q3(b): triangle A(1,1) B(6,2) C(3,7) ==");
  const A = [1, 1], B = [6, 2], C = [3, 7];
  const total = edge(...A, ...B, ...C);
  assert(total === 28, `total ${total}`);
  console.log(`  total = E_AB(C) = ${total}, area = ${total / 2}`);
  // shoelace with y read as UP: positive means counter-clockwise on paper
  const shoelace = (A[0] * B[1] - B[0] * A[1]) + (B[0] * C[1] - C[0] * B[1]) + (C[0] * A[1] - A[0] * C[1]);
  assert(shoelace === 28, "shoelace");
  console.log("  y up: CCW (shoelace +28);  y down (screen): the same order reads CW");
  const E = (P) => [edge(...A, ...B, ...P), edge(...B, ...C, ...P), edge(...C, ...A, ...P)];
  const want = { "3,3": [8, 12, 8], "5,5": [16, -4, 16], "1,4": [15, 19, -6] };
  for (const [k, v] of Object.entries(want)) {
    const P = k.split(",").map(Number), got = E(P);
    assert(eq(got, v), `E(${k}) ${got}`);
    console.log(`  P(${k}): (E_AB, E_BC, E_CA) = (${got.join(", ")})  ${got.every((e) => e >= 0) ? "inside" : "outside"}`);
  }
  console.log("== Q3(c): barycentric of P1 ==");
  const [la, lb, lc] = barycentric(A, B, C, [3, 3]);
  close(la, 3 / 7); close(lb, 2 / 7); close(lc, 2 / 7); close(la + lb + lc, 1);
  const rx = la * A[0] + lb * B[0] + lc * C[0], ry = la * A[1] + lb * B[1] + lc * C[1];
  close(rx, 3, 1e-12); close(ry, 3, 1e-12);
  console.log(`  (lA, lB, lC) = (12/28, 8/28, 8/28) = (3/7, 2/7, 2/7);  lA*A + lB*B + lC*C = (${rx.toFixed(12)}, ${ry.toFixed(12)})`);
  const v = 0.5 * 10 + 0.25 * 20 + 0.25 * 40;
  assert(v === 20, "E5");
  console.log(`  Example E5: 0.5*10 + 0.25*20 + 0.25*40 = ${v}`);

  console.log("== Q3(d): two triangles sharing the diagonal of a 6x6 square ==");
  const T1 = [[2, 2], [8, 2], [8, 8]], T2 = [[2, 2], [8, 8], [2, 8]];
  const ge = coverage(12, 12, [T1, T2], { topLeft: false });
  const gt = coverage(12, 12, [T1, T2], { topLeft: false, strictGreater: true });
  const tl = coverage(12, 12, [T1, T2], { topLeft: true });
  const twiceAt = [], gapAt = [];
  for (let i = 0; i < 144; i++) {
    if (ge.counts[i] >= 2) twiceAt.push([i % 12, (i / 12) | 0]);
    if (gt.counts[i] === 0 && ge.counts[i] > 0) gapAt.push([i % 12, (i / 12) | 0]);
  }
  const diag = [2, 3, 4, 5, 6, 7].map((k) => [k, k]);
  assert(eq(twiceAt, diag) && eq(gapAt, diag), "diagonal pixels");
  assert(ge.twice === 6 && gt.gaps === 6 && tl.once === 36 && tl.twice === 0 && tl.gaps === 0, "coverage");
  console.log(`  >= 0 : twice=${ge.twice} at ${twiceAt.map((p) => `(${p})`).join(" ")}`);
  console.log(`  >  0 : gaps=${gt.gaps} at the same pixels`);
  console.log(`  top-left: once=${tl.once} twice=${tl.twice} gaps=${tl.gaps}`);
}

function q4() {
  console.log("== Q4 / E1: sample centre vs corner ==");
  const lit = (inside) => {
    const out = [];
    for (let y = 0; y < 6; y++) for (let x = 0; x < 6; x++) if (inside(x, y)) out.push([x, y]);
    return out;
  };
  const centre = lit((x, y) => x + 0.5 >= 1 && x + 0.5 < 3 && y + 0.5 >= 1 && y + 0.5 < 3);
  const corner = lit((x, y) => x >= 1 && x <= 3 && y >= 1 && y <= 3);
  assert(eq(centre, [[1, 1], [2, 1], [1, 2], [2, 2]]) && corner.length === 9, "E1");
  console.log(`  centre rule: ${centre.length} pixels ${centre.map((p) => `(${p})`).join(" ")}`);
  console.log(`  corner test, inclusive: ${corner.length} pixels (x, y in 1..3)`);

  // D3D9: pixel i has its centre at integer i. A quad from 0 to 4 carrying
  // u = 0..1 over a 4-texel texture gives texel-space coordinate u*4 - 0.5.
  const weights = (s) => { const f = s - Math.floor(s); return [1 - f, f]; };
  for (const [label, shift] of [["no offset", 0], ["-0.5 offset", -0.5]]) {
    const i = 1, u = (i - shift) / 4, s = u * 4 - 0.5;
    const [w0, w1] = weights(s);
    const per = [w0 * w0, w0 * w1, w1 * w0, w1 * w1].filter((w) => w > 0);
    console.log(`  ${label}: texel coord ${s}, ${per.length} texel(s), weights ${per.join(", ")}`);
    if (shift === 0) assert(per.length === 4 && per.every((w) => w === 0.25), "D3D9 blur");
    else assert(per.length === 1 && per[0] === 1, "D3D9 exact");
  }
}

q2();
q3();
q4();
console.log("\nALL STUDI PENDAHULUAN NUMBERS CHECKED");
