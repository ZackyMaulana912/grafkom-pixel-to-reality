/* Module 2 -- forward (rasterise the polylines) vs backward (for every screen
 * pixel, distance-test every segment) drawing of the plan, at zoom 1x and 10x.
 *
 * This is the "decision defended with a prediction" task: write your expected
 * ordering FIRST (Lab 3), then run this and reconcile. Absolute ms vary by
 * machine; the RATIO and its direction are the result.
 *
 * Every (method, zoom) pair is warmed up BEFORE any timing, and the timings
 * are taken in interleaved rounds and reported as the median. Without that,
 * whichever zoom is timed first also pays for V8 optimising the loop, and
 * zoom 10x looks faster than 1x only because it runs second.
 *
 *   node bench.mjs [--plan myplan.json --w 800 --h 600 --iters 20 --warmup 3 --rounds 5]
 */
import { loadPlan, makeWorldToScreen } from "./plan.mjs";
import { Framebuffer, lineBresenham } from "./raster.mjs";

const val = (k, d) => {
  const i = process.argv.indexOf(k);
  return i >= 0 && process.argv[i + 1] ? +process.argv[i + 1] : d;
};
const W = val("--w", 800), H = val("--h", 600), ITERS = val("--iters", 20), WARMUP = val("--warmup", 3);
const ROUNDS = val("--rounds", 5);
const pi = process.argv.indexOf("--plan");
const planPath = pi >= 0 ? process.argv[pi + 1] : "pusaka_plan.json";
const plan = loadPlan(planPath);

// flatten the plan into screen-space segments at a given zoom
function segmentsAtZoom(zoom) {
  const w2s = makeWorldToScreen(plan, H);
  const segs = [];
  for (const pl of plan.polylines) {
    const pts = pl.points.map(([x, y]) => {
      const [sx, sy] = w2s([x, y]);
      return [(sx - W / 2) * zoom + W / 2, (sy - H / 2) * zoom + H / 2];
    });
    for (let i = 0; i + 1 < pts.length; i++) segs.push([pts[i], pts[i + 1]]);
    if (pl.closed && pts.length > 2) segs.push([pts[pts.length - 1], pts[0]]);
  }
  return segs;
}

const forward = (fb, segs) => {
  for (const [a, b] of segs) lineBresenham(a[0] | 0, a[1] | 0, b[0] | 0, b[1] | 0, fb, [255, 255, 255]);
};

const backward = (fb, segs) => {
  // for each pixel, light it if within 0.75 px of any segment
  for (let y = 0; y < fb.h; y++)
    for (let x = 0; x < fb.w; x++) {
      const px = x + 0.5, py = y + 0.5;
      for (const [a, b] of segs) {
        const vx = b[0] - a[0], vy = b[1] - a[1];
        const wx = px - a[0], wy = py - a[1];
        const L2 = vx * vx + vy * vy || 1e-9;
        let t = (wx * vx + wy * vy) / L2;
        t = t < 0 ? 0 : t > 1 ? 1 : t;
        const dx = wx - t * vx, dy = wy - t * vy;
        if (dx * dx + dy * dy <= 0.5625) { fb.set(x, y, [255, 255, 255]); break; }
      }
    }
};

function time(fn, segs) {
  const t0 = performance.now();
  for (let i = 0; i < ITERS; i++) fn(new Framebuffer(W, H), segs);
  return (performance.now() - t0) / ITERS;
}

console.log(`plan ${planPath}: ${segmentsAtZoom(1).length} segments   framebuffer ${W}x${H}   iters ${ITERS}`);
const ZOOMS = [1, 10];
for (let k = 0; k < WARMUP; k++)
  for (const zoom of ZOOMS)
    for (const fn of [forward, backward]) fn(new Framebuffer(W, H), segmentsAtZoom(zoom));
const median = (xs) => [...xs].sort((p, q) => p - q)[xs.length >> 1];
const ms = Object.fromEntries(ZOOMS.map((z) => [z, { f: [], b: [] }]));
for (let r = 0; r < ROUNDS; r++)
  for (const zoom of ZOOMS) {
    const segs = segmentsAtZoom(zoom);
    ms[zoom].f.push(time(forward, segs));
    ms[zoom].b.push(time(backward, segs));
  }
console.log(`${"zoom".padEnd(8)}${"forward (ms)".padEnd(16)}${"backward (ms)".padEnd(16)}ratio (bwd/fwd)   [median of ${ROUNDS} rounds]`);
for (const zoom of ZOOMS) {
  const f = median(ms[zoom].f), b = median(ms[zoom].b);
  const spread = `backward ${Math.min(...ms[zoom].b).toFixed(1)}..${Math.max(...ms[zoom].b).toFixed(1)}`;
  console.log(`${String(zoom + "x").padEnd(8)}${f.toFixed(3).padEnd(16)}${b.toFixed(3).padEnd(16)}${(b / f).toFixed(1)}x`.padEnd(58) + spread);
}
// both timings include allocating the framebuffer; show that share on its own
const alloc = time(() => {}, []);
console.log(`framebuffer allocation alone: ${alloc.toFixed(3)} ms per frame`);
console.log("\nInterpret: forward cost tracks total segment length (pixels drawn);");
console.log("backward cost tracks pixels x segments and is ~flat in zoom.");
