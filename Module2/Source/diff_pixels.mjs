/* Module 2 -- explain every pixel where two renders of a plan disagree
 * (Lab 3 no 2: "jelaskan setiap pixel yang tidak cocok"). Each mismatch is
 * tied to the plan segments within 1 px of it and classified:
 *   end      : within 1 px of a segment's end point (a free end, or where two
 *              lines meet / one line stops on another)
 *   diagonal : on a segment that is neither horizontal nor vertical
 *   other    : anything else (should be empty; printed in full)
 *
 *   node diff_pixels.mjs out/plan_scratch.ppm plan_three.ppm [--plan myplan.json]
 */
import { Framebuffer } from "./raster.mjs";
import { loadPlan, makeWorldToScreen } from "./plan.mjs";

const files = process.argv.slice(2).filter((s) => !s.startsWith("--") && !s.endsWith(".json"));
const pi = process.argv.indexOf("--plan");
const plan = loadPlan(pi >= 0 ? process.argv[pi + 1] : "myplan.json");
const [A, B] = files.map((f) => Framebuffer.readPPM(f));
if (A.w !== B.w || A.h !== B.h) throw new Error("size mismatch");

const w2s = makeWorldToScreen(plan, A.h);
const segs = [];
for (const pl of plan.polylines) {
  const p = pl.points.map(w2s);
  if (pl.closed) p.push(p[0]);
  for (let i = 0; i + 1 < p.length; i++) segs.push({ id: pl.id, a: p[i], b: p[i + 1] });
}
function near(x, y) {
  const out = [];
  for (const s of segs) {
    const vx = s.b[0] - s.a[0], vy = s.b[1] - s.a[1], L2 = vx * vx + vy * vy || 1;
    const t = Math.max(0, Math.min(1, ((x - s.a[0]) * vx + (y - s.a[1]) * vy) / L2));
    const d = Math.hypot(x - (s.a[0] + t * vx), y - (s.a[1] + t * vy));
    if (d <= 1) out.push({ s, d });
  }
  return out.sort((p, q) => p.d - q.d);
}

const groups = { end: [], diagonal: [], other: [] };
for (let y = 0; y < A.h; y++)
  for (let x = 0; x < A.w; x++) {
    const a = A.get(x, y), b = B.get(x, y);
    if (a[0] === b[0] && a[1] === b[1] && a[2] === b[2]) continue;
    const hits = near(x, y);
    const atEnd = hits.some(({ s }) => [s.a, s.b].some((p) => Math.hypot(x - p[0], y - p[1]) <= 1));
    const diag = hits.some(({ s }) => s.a[0] !== s.b[0] && s.a[1] !== s.b[1]);
    const g = atEnd ? "end" : diag ? "diagonal" : "other";
    const ids = [...new Set(hits.map((h) => h.s.id))].join("+") || "no segment within 1 px";
    groups[g].push(`(${x},${y}) ${a.join(",")} vs ${b.join(",")}  ${ids}`);
  }

const total = groups.end.length + groups.diagonal.length + groups.other.length;
console.log(`${total} mismatched pixels`);
for (const [g, list] of Object.entries(groups)) {
  console.log(`\n${g}: ${list.length}`);
  for (const line of list) console.log(`  ${line}`);
}
