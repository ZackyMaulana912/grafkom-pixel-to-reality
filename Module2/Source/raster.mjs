/* Module 2 -- from-scratch 2D rasteriser. Plain JavaScript, no framework,
 * no <canvas>: the framebuffer is a typed array. The SAME functions drive a
 * browser <canvas> via ctx.putImageData(new ImageData(fb.rgba(), w, h)).
 *
 * CONVENTION (stated once, never mixed):
 *   - y is DOWN (screen / image row order).
 *   - a pixel (x,y) is a POINT SAMPLE at (x+0.5, y+0.5).
 *   - inside a triangle = all three edge functions >= 0 with the vertices in
 *     the order whose total edge(A,B,C) > 0; triangle() puts them in that
 *     order itself, so a caller cannot lose a triangle to its winding.
 *   - the exactly-on-edge (== 0) case is decided by the module's top-left
 *     rule (section 9), on integer fixed-point values so that "== 0" is an
 *     exact test. Note: with y down and total > 0 the triangle runs CLOCKWISE
 *     on screen, so that rule hands on-edge pixels to the bottom and right
 *     edges. A GPU gives them to the top and left edges; fillRule "gpu"
 *     reproduces that (checked against WebGL, see web/gpu_rule.html).
 *
 * Reproduces:
 *   Example E1      : fillRect centre rule lights (1,1),(2,1),(1,2),(2,2)
 *   Example E2 / E3 : lineDDA and lineBresenham on (2,1)->(9,5) give
 *     [(2,1),(3,2),(4,2),(5,3),(6,3),(7,4),(8,4),(9,5)]
 *   Example E4      : edge signs for A(1,1) B(6,2) C(3,7)
 *   Example E5      : barycentric interpolation 10/20/40 at (.5,.25,.25) -> 20
 */
import { readFileSync, writeFileSync } from "node:fs";

const WHITE = [255, 255, 255];

// ---------------------------------------------------------------- Framebuffer
export class Framebuffer {
  constructor(w, h, bg = [0, 0, 0]) {
    this.w = w;
    this.h = h;
    this.data = new Uint8ClampedArray(w * h * 3);
    if (bg[0] || bg[1] || bg[2]) this.clear(bg);
  }
  clear(rgb) {
    for (let i = 0; i < this.data.length; i += 3) {
      this.data[i] = rgb[0]; this.data[i + 1] = rgb[1]; this.data[i + 2] = rgb[2];
    }
  }
  inside(x, y) { return x >= 0 && y >= 0 && x < this.w && y < this.h; }
  set(x, y, rgb) {
    if (!this.inside(x, y)) return;
    const i = (y * this.w + x) * 3;
    this.data[i] = rgb[0]; this.data[i + 1] = rgb[1]; this.data[i + 2] = rgb[2];
  }
  get(x, y) {
    const i = (y * this.w + x) * 3;
    return [this.data[i], this.data[i + 1], this.data[i + 2]];
  }
  // P6 binary PPM: text header then raw RGB bytes (same family as Module 1)
  writePPM(path) {
    const header = Buffer.from(`P6\n${this.w} ${this.h}\n255\n`, "ascii");
    writeFileSync(path, Buffer.concat([header, Buffer.from(this.data.buffer, 0, this.data.length)]));
    return header.length + this.data.length;
  }
  static readPPM(path) {
    const buf = readFileSync(path);
    let p = 0;
    const tok = () => {
      while (p < buf.length && /\s/.test(String.fromCharCode(buf[p]))) p++;
      let s = "";
      while (p < buf.length && !/\s/.test(String.fromCharCode(buf[p]))) s += String.fromCharCode(buf[p++]);
      return s;
    };
    const magic = tok();
    if (magic !== "P6") throw new Error(`${path}: not a P6 PPM (got ${magic})`);
    const w = +tok(), h = +tok(), maxv = +tok();
    if (maxv !== 255) throw new Error(`${path}: maxval ${maxv} != 255`);
    p++; // single whitespace after maxval
    const fb = new Framebuffer(w, h);
    fb.data.set(buf.subarray(p, p + w * h * 3));
    return fb;
  }
}

// ------------------------------------------------------- sample-centre rect
/**
 * Fill the rectangle [x0,x1) x [y0,y1) and return the lit pixels.
 * sample: "centre" tests (x+0.5, y+0.5) -- the convention of this file;
 * "corner" tests (x, y) half-open; "corner-inclusive" tests x0 <= x <= x1,
 * the off-by-one of looping `x <= maxX` on corners (Example E1b).
 */
export function fillRect(fb, x0, y0, x1, y1, rgb = WHITE, { sample = "centre" } = {}) {
  const lit = [];
  const inX = {
    centre: (x, lo, hi) => x + 0.5 >= lo && x + 0.5 < hi,
    corner: (x, lo, hi) => x >= lo && x < hi,
    "corner-inclusive": (x, lo, hi) => x >= lo && x <= hi,
  }[sample];
  if (!inX) throw new Error(`fillRect: unknown sample mode ${sample}`);
  const W = fb ? fb.w : Math.ceil(x1) + 1, H = fb ? fb.h : Math.ceil(y1) + 1;
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++)
      if (inX(x, x0, x1) && inX(y, y0, y1)) {
        lit.push([x, y]);
        if (fb) fb.set(x, y, rgb);
      }
  return lit;
}

// --------------------------------------------------------------------- lines
/**
 * DDA: step the long axis by 1 and the short axis by the slope, rounding each
 * point. Position k is computed from k (not accumulated), so no drift.
 */
export function lineDDA(x0, y0, x1, y1, fb = null, rgb = WHITE) {
  const dx = x1 - x0, dy = y1 - y0;
  const steps = Math.max(Math.abs(dx), Math.abs(dy));
  const pts = [];
  for (let k = 0; k <= steps; k++) {
    const x = steps === 0 ? x0 : x0 + (k * dx) / steps;
    const y = steps === 0 ? y0 : y0 + (k * dy) / steps;
    const p = [Math.round(x), Math.round(y)];
    pts.push(p);
    if (fb) fb.set(p[0], p[1], rgb);
  }
  return pts;
}

/**
 * Bresenham with the decision variable of Example E3 (D0 = 2dy - dx), made
 * octant-free by walking the longer axis ("fast") and stepping the shorter
 * ("slow") only when D > 0. Integer add / compare only.
 */
export function lineBresenham(x0, y0, x1, y1, fb = null, rgb = WHITE) {
  x0 |= 0; y0 |= 0; x1 |= 0; y1 |= 0;
  const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
  const sx = x1 >= x0 ? 1 : -1, sy = y1 >= y0 ? 1 : -1;
  const steep = dy > dx;
  const fast = steep ? dy : dx, slow = steep ? dx : dy;
  let D = 2 * slow - fast;
  let x = x0, y = y0;
  const pts = [];
  for (let i = 0; i <= fast; i++) {
    pts.push([x, y]);
    if (fb) fb.set(x, y, rgb);
    if (D > 0) {
      if (steep) x += sx; else y += sy;
      D += 2 * (slow - fast);
    } else {
      D += 2 * slow;
    }
    if (steep) y += sy; else x += sx;
  }
  return pts;
}

export function polyline(fb, pts, rgb, close = false) {
  for (let i = 0; i + 1 < pts.length; i++)
    lineBresenham(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], fb, rgb);
  if (close && pts.length > 2) {
    const a = pts[pts.length - 1], b = pts[0];
    lineBresenham(a[0], a[1], b[0], b[1], fb, rgb);
  }
}

// ----------------------------------------------------------------- triangles
/** Edge function of directed edge A->B at P: twice the signed area of ABP. */
export const edge = (ax, ay, bx, by, px, py) =>
  (bx - ax) * (py - ay) - (by - ay) * (px - ax);

/**
 * The module's "before": float edge functions at the sample centre, inside if
 * all three are >= 0 (or > 0), no top-left rule and no winding fix -- a
 * triangle passed in the other order draws nothing.
 */
export function triangleNaive(fb, A, B, C, rgb = WHITE, { strictGreater = false, onFragment = null } = {}) {
  const pass = strictGreater ? (v) => v > 0 : (v) => v >= 0;
  const minX = Math.max(0, Math.floor(Math.min(A[0], B[0], C[0])));
  const maxX = Math.min(fb.w - 1, Math.ceil(Math.max(A[0], B[0], C[0])));
  const minY = Math.max(0, Math.floor(Math.min(A[1], B[1], C[1])));
  const maxY = Math.min(fb.h - 1, Math.ceil(Math.max(A[1], B[1], C[1])));
  let lit = 0;
  for (let y = minY; y <= maxY; y++)
    for (let x = minX; x <= maxX; x++) {
      const px = x + 0.5, py = y + 0.5;
      if (pass(edge(...B, ...C, px, py)) && pass(edge(...C, ...A, px, py)) && pass(edge(...A, ...B, px, py))) {
        lit++;
        if (typeof fb.set === "function") fb.set(x, y, rgb);
        if (onFragment) onFragment(x, y);
      }
    }
  return lit;
}

// Vertices snap to a 1/256-pixel grid (a GPU uses a few sub-pixel bits the
// same way). The sample centre (x + 0.5) * SUB is then an integer, every edge
// value is an integer, and "E > 0" is exactly "E - 1 >= 0". With the centre
// left at x + 0.5, E can be 0.5 and a -1 bias wrongly drops the pixel.
const SUB = 256;

/**
 * Does directed edge X->Y (y down, total > 0) own the pixels exactly on it?
 * "module": section 9 of the module -- top if dy == 0 and dx < 0, left if
 *   dy > 0. On a clockwise-on-screen triangle these are the bottom and right
 *   edges (the formula is the top-left rule written for the other winding).
 * "gpu": the mirror image, the visual top and left edges, as WebGL draws it.
 */
function ownsEdge(X, Y, fillRule) {
  const dx = Y[0] - X[0], dy = Y[1] - X[1];
  if (fillRule === "gpu") return (dy === 0 && dx > 0) || dy < 0;
  return (dy === 0 && dx < 0) || dy > 0;
}

/**
 * Fill triangle A,B,C (each [x,y], any winding) with rgb; returns pixels lit.
 * opts.topLeft (default true): apply the top-left rule.
 * opts.fillRule ("module" | "gpu", default "module"): which edges own the
 *   on-edge pixels, see ownsEdge().
 * opts.strictGreater (default false): ">" on every edge (the crack bug).
 * opts.onFragment(x,y,lA,lB,lC): per covered pixel, with its barycentric
 *   weights (for coverage counts here; depth and UV in Module 3).
 */
export function triangle(fb, A, B, C, rgb = WHITE, opts = {}) {
  const { topLeft = true, fillRule = "module", strictGreater = false, onFragment = null } = opts;
  if (fillRule !== "module" && fillRule !== "gpu") throw new Error(`triangle: unknown fillRule ${fillRule}`);
  const canDraw = !!(fb && typeof fb.set === "function");
  const W = fb ? fb.w : Infinity, H = fb ? fb.h : Infinity;
  const snap = (V) => [Math.round(V[0] * SUB), Math.round(V[1] * SUB)];
  let a = snap(A), b = snap(B), c = snap(C);
  let area = edge(...a, ...b, ...c);
  if (area === 0) return 0;
  const flipped = area < 0;
  if (flipped) { [b, c] = [c, b]; area = -area; }

  const bias = (X, Y) => (strictGreater ? -1 : !topLeft ? 0 : ownsEdge(X, Y, fillRule) ? 0 : -1);
  const edges = [[b, c], [c, a], [a, b]].map(([X, Y]) => ({
    X, Y, bias: bias(X, Y),
    stepX: -(Y[1] - X[1]) * SUB,   // E grows by this per pixel to the right
    stepY: (Y[0] - X[0]) * SUB,    // ... and by this per pixel down
  }));

  const minX = Math.max(0, Math.floor(Math.min(a[0], b[0], c[0]) / SUB));
  const maxX = Math.min(W - 1, Math.ceil(Math.max(a[0], b[0], c[0]) / SUB));
  const minY = Math.max(0, Math.floor(Math.min(a[1], b[1], c[1]) / SUB));
  const maxY = Math.min(H - 1, Math.ceil(Math.max(a[1], b[1], c[1]) / SUB));
  const half = SUB / 2;
  const row = edges.map((e) => edge(...e.X, ...e.Y, minX * SUB + half, minY * SUB + half));

  let lit = 0;
  for (let y = minY; y <= maxY; y++) {
    let [eA, eB, eC] = row;
    for (let x = minX; x <= maxX; x++) {
      if (eA + edges[0].bias >= 0 && eB + edges[1].bias >= 0 && eC + edges[2].bias >= 0) {
        lit++;
        if (canDraw) fb.set(x, y, rgb);
        // weights are reported in the caller's vertex order, flipped or not
        if (onFragment) {
          if (flipped) onFragment(x, y, eA / area, eC / area, eB / area);
          else onFragment(x, y, eA / area, eB / area, eC / area);
        }
      }
      eA += edges[0].stepX; eB += edges[1].stepX; eC += edges[2].stepX;
    }
    for (let k = 0; k < 3; k++) row[k] += edges[k].stepY;
  }
  return lit;
}

/** Barycentric coords of P in triangle A,B,C (unbiased). Sum to 1. */
export function barycentric(A, B, C, P) {
  const total = edge(A[0], A[1], B[0], B[1], C[0], C[1]);
  if (total === 0) throw new Error("barycentric: degenerate triangle");
  return [
    edge(B[0], B[1], C[0], C[1], P[0], P[1]) / total,
    edge(C[0], C[1], A[0], A[1], P[0], P[1]) / total,
    edge(A[0], A[1], B[0], B[1], P[0], P[1]) / total,
  ];
}

/**
 * Coverage map for a set of triangles: how many times each pixel is filled.
 * Returns { once, twice, gaps, counts } where `gaps` counts pixels that are
 * inside the exact geometric union (unbiased >=0 test) but filled 0 times.
 */
export function coverage(w, h, tris, opts = {}) {
  const counts = new Int32Array(w * h);
  for (const [A, B, C] of tris)
    triangle({ w, h }, A, B, C, null, {
      ...opts,
      onFragment: (x, y) => { counts[y * w + x]++; },
    });
  // geometric union: unbiased, non-strict, no top-left rule
  const union = new Uint8Array(w * h);
  for (const [A, B, C] of tris)
    triangle({ w, h }, A, B, C, null, {
      topLeft: false, strictGreater: false,
      onFragment: (x, y) => { union[y * w + x] = 1; },
    });
  let once = 0, twice = 0, gaps = 0;
  for (let i = 0; i < counts.length; i++) {
    if (counts[i] === 1) once++;
    else if (counts[i] >= 2) twice++;
    if (union[i] && counts[i] === 0) gaps++;
  }
  return { once, twice, gaps, counts };
}
