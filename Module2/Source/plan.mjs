/* Module 2 -- load a floor plan (metres, y-up) and render it as 2D primitives.
 * The single worldToScreen() has the y-flip and origin baked in -- it lives in
 * plan_common.mjs so the web viewer uses the very same function, and it is
 * unit-tested in tests.mjs on a known point. */
import { readFileSync } from "node:fs";
import { Framebuffer, polyline, triangle } from "./raster.mjs";
import { categoryColours, makeWorldToScreen } from "./plan_common.mjs";

export { VIRIDIS5, DEFAULT_LEGEND, legendOf, categoryColours, makeWorldToScreen } from "./plan_common.mjs";
export const CATEGORY_RGB = categoryColours({});

export function loadPlan(path = "pusaka_plan.json") {
  return JSON.parse(readFileSync(path, "utf8"));
}

export function renderPlan(fb, plan, { fillSilhouette = false } = {}) {
  const w2s = makeWorldToScreen(plan, fb.h);
  if (fillSilhouette && plan.silhouette) {
    const p = plan.silhouette.points.map(w2s);
    // fan-triangulate the (convex) footprint
    for (let i = 1; i + 1 < p.length; i++) {
      let A = p[0], B = p[i], C = p[i + 1];
      // ensure total > 0 for our convention; swap B,C if not
      const tot = (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0]);
      if (tot < 0) [B, C] = [C, B];
      triangle(fb, A, B, C, [230, 236, 245]);
    }
  }
  const colours = categoryColours(plan);
  let segs = 0;
  for (const pl of plan.polylines) {
    const pts = pl.points.map(w2s);
    const rgb = colours[pl.category] || [255, 255, 255];
    polyline(fb, pts, rgb, !!pl.closed);
    segs += pl.points.length - 1 + (pl.closed ? 1 : 0);
  }
  return segs;
}

export function newFramebufferForPlan(plan, w, h) {
  const fb = new Framebuffer(w, h, [18, 18, 22]);
  return fb;
}
