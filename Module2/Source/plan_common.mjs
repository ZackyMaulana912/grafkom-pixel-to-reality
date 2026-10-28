/* Module 2 -- the parts of a floor plan both renderers must agree on: the
 * legend colours and the one world -> screen mapping. Shared by plan.mjs
 * (Node) and web/viewer.mjs (browser). No imports, so it loads in both. */

// viridis 5-step ramp (luminance varies -> CVD- and grayscale-safe, Module 1)
export const VIRIDIS5 = [
  [68, 1, 84],
  [59, 82, 139],
  [33, 145, 140],
  [94, 201, 98],
  [253, 231, 37],
];

// pusaka_plan.json has no legend block; these are its five categories in ramp order
export const DEFAULT_LEGEND = [
  { category: "wall", label: "wall", marker: "■" },
  { category: "cella", label: "cella", marker: "◆" },
  { category: "stair", label: "stair", marker: "▲" },
  { category: "shrine", label: "shrine", marker: "●" },
  { category: "axis", label: "axis", marker: "‖" },
];

/** The plan's legend (its own block if present), one viridis step per entry. */
export function legendOf(plan) {
  const legend = plan.legend ?? DEFAULT_LEGEND;
  if (legend.length > VIRIDIS5.length) throw new Error(`legend has ${legend.length} categories, ramp has 5`);
  return legend.map((e, i) => ({ ...e, rgb: VIRIDIS5[i] }));
}

/** category -> rgb for a plan; unknown categories stay white. */
export function categoryColours(plan) {
  return Object.fromEntries(legendOf(plan).map((e) => [e.category, e.rgb]));
}

/** metres (y-up) -> screen pixels (y-down), given the plan's scale + origin
 * and the framebuffer height. Deterministic; the ONLY place the flip lives. */
export function makeWorldToScreen(plan, H) {
  const s = plan.scale_px_per_m;
  const [ox, oy] = plan.origin_m;
  return ([xm, ym]) => [
    Math.round((xm + ox) * s),
    Math.round(H - 1 - (ym + oy) * s),
  ];
}
