/* Module 2 -- follow ONE wall segment of a plan through the seven pipeline
 * stages and print the real numbers at every stage (Lab 1 no 3, A1).
 *
 *   node walkthrough.mjs [--plan myplan.json --id outer_wall --seg 1 --w 800 --h 600]
 */
import { loadPlan, makeWorldToScreen, categoryColours, renderPlan, newFramebufferForPlan } from "./plan.mjs";
import { lineBresenham } from "./raster.mjs";

const opt = (k, d) => { const i = process.argv.indexOf(k); return i >= 0 ? process.argv[i + 1] : d; };
const planPath = opt("--plan", "myplan.json"), id = opt("--id", "outer_wall");
const seg = +opt("--seg", 1), W = +opt("--w", 800), H = +opt("--h", 600);

const plan = loadPlan(planPath);
const pl = plan.polylines.find((p) => p.id === id);
if (!pl) throw new Error(`no polyline "${id}" in ${planPath}`);
const pts = pl.closed ? [...pl.points, pl.points[0]] : pl.points;
if (seg < 0 || seg + 1 >= pts.length) throw new Error(`segment ${seg} out of range for "${id}"`);
const [P, Q] = [pts[seg], pts[seg + 1]];

console.log(`1 application      "${id}" segment ${seg}: (${P}) m -> (${Q}) m, category "${pl.category}"`);

const s = plan.scale_px_per_m, [ox, oy] = plan.origin_m;
const exact = ([x, y]) => [(x + ox) * s, H - 1 - (y + oy) * s];
const w2s = makeWorldToScreen(plan, H);
const [a, b] = [w2s(P), w2s(Q)];
console.log(`2 vertex processing x_px = (x_m + ${ox}) * ${s},  y_px = ${H - 1} - (y_m + ${oy}) * ${s}`);
console.log(`                   (${exact(P).map((v) => +v.toFixed(3))}) -> rounded (${a})`);
console.log(`                   (${exact(Q).map((v) => +v.toFixed(3))}) -> rounded (${b})`);

const inside = ([x, y]) => x >= 0 && y >= 0 && x < W && y < H;
console.log(`3 assembly/clipping two vertices -> one line primitive; both inside ${W}x${H}: ${inside(a) && inside(b)} (nothing clipped)`);

const pix = lineBresenham(a[0], a[1], b[0], b[1]);
const dx = Math.abs(b[0] - a[0]), dy = Math.abs(b[1] - a[1]);
console.log(`4 rasterisation    Bresenham: dx=${dx} dy=${dy}, ${pix.length} pixels = max(dx,dy)+1, ` +
  `first (${pix[0]}) last (${pix[pix.length - 1]})`);
const show = pix.length <= 12 ? pix : [...pix.slice(0, 4), "...", ...pix.slice(-4)];
console.log(`                   ${show.map((p) => (p === "..." ? p : `(${p})`)).join(" ")}`);

const rgb = categoryColours(plan)[pl.category];
console.log(`5 fragment shading flat colour of "${pl.category}" = rgb(${rgb})  (viridis step, no lighting)`);
console.log(`6 per-fragment ops no depth test, no blending: the later write wins (lines are drawn after the fill)`);

const fb = newFramebufferForPlan(plan, W, H);
renderPlan(fb, plan, { fillSilhouette: true });
const mid = pix[(pix.length / 2) | 0];
const probe = (x, y) => `(${x},${y}) = rgb(${fb.get(x, y)})`;
console.log(`7 framebuffer      ${probe(...mid)}  neighbours ${probe(mid[0], mid[1] - 1)}  ${probe(mid[0], mid[1] + 1)}`);
