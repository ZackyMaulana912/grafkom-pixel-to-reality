/* Module 2 -- octant check (Lab 2 no 5): a 24-spoke asterisk, one Bresenham
 * line every 15 degrees from one centre. A wrong octant shows up as a spoke
 * that is too short, too long, or wanders off its ideal line.
 *
 * "Same length" is read as: the last pixel of every spoke lies R +/- 1 px
 * (Euclidean) from the centre. The PIXEL COUNT differs per angle by design,
 * max(|dx|,|dy|) + 1, so a diagonal spoke has about 0.71x the pixels of a
 * horizontal one at the same length.
 *
 *   node draw_asterisk.mjs [--r 110]
 */
import { mkdirSync } from "node:fs";
import { Framebuffer, lineBresenham } from "./raster.mjs";

/** spokes of an n-spoke asterisk around (cx, cy) with radius R, y down */
export function asterisk(cx, cy, R, n = 24) {
  const spokes = [];
  for (let k = 0; k < n; k++) {
    const deg = (360 / n) * k, t = (deg * Math.PI) / 180;
    // y is down on screen, so +sin moves the end UP the way a protractor reads
    const end = [Math.round(cx + R * Math.cos(t)), Math.round(cy - R * Math.sin(t))];
    const pts = lineBresenham(cx, cy, end[0], end[1]);
    const last = pts[pts.length - 1];
    const reach = Math.hypot(last[0] - cx, last[1] - cy);
    // largest distance of any pixel from the ideal segment, along the slow axis
    const fx = end[0] - cx, fy = end[1] - cy, xMajor = Math.abs(fx) >= Math.abs(fy);
    let wander = 0;
    for (const [x, y] of pts) {
      const d = xMajor ? Math.abs(y - (cy + (fy * (x - cx)) / fx)) : Math.abs(x - (cx + (fx * (y - cy)) / fy));
      wander = Math.max(wander, d);
    }
    spokes.push({ deg, end, pixels: pts.length, expected: Math.max(Math.abs(fx), Math.abs(fy)) + 1, reach, wander, pts });
  }
  return spokes;
}

if (process.argv[1] && process.argv[1].endsWith("draw_asterisk.mjs")) {
  const ri = process.argv.indexOf("--r");
  const R = ri >= 0 ? +process.argv[ri + 1] : 110;
  const S = 2 * R + 21, c = R + 10;
  const fb = new Framebuffer(S, S, [18, 18, 22]);
  const spokes = asterisk(c, c, R);
  console.log(`24 spokes, centre (${c},${c}), R = ${R} px`);
  console.log("deg   end         pixels  reach    |reach-R|  wander");
  for (const s of spokes) {
    for (const [x, y] of s.pts) fb.set(x, y, [253, 231, 37]);
    console.log(`${String(s.deg).padStart(3)}  (${s.end})`.padEnd(18) +
      `${String(s.pixels).padStart(5)}  ${s.reach.toFixed(3).padStart(8)}  ${Math.abs(s.reach - R).toFixed(3).padStart(8)}   ${s.wander.toFixed(3)}`);
  }
  fb.set(c, c, [230, 30, 30]);
  const worst = Math.max(...spokes.map((s) => Math.abs(s.reach - R)));
  const lens = spokes.map((s) => s.pixels);
  console.log(`worst |reach - R| = ${worst.toFixed(3)} px  (pass if <= 1)`);
  console.log(`pixel counts ${Math.min(...lens)}..${Math.max(...lens)}; every spoke = max(|dx|,|dy|)+1: ` +
    `${spokes.every((s) => s.pixels === s.expected)}; max wander ${Math.max(...spokes.map((s) => s.wander)).toFixed(3)} px`);
  mkdirSync("out", { recursive: true });
  fb.writePPM("out/asterisk.ppm");
  console.log("wrote out/asterisk.ppm");
}
