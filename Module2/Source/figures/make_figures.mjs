/* Module 2 -- diagrams for the Studi Pendahuluan, written as plain SVG.
 * No dependency: every lit pixel shown is computed by raster.mjs itself, so a
 * figure can never disagree with the code.
 *
 *   node figures/make_figures.mjs [--out ../docs/studi-pendahuluan/img]
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { lineBresenham, lineDDA, edge, triangle, coverage } from "../raster.mjs";

const outIdx = process.argv.indexOf("--out");
const OUT = outIdx >= 0 ? process.argv[outIdx + 1] : "../docs/studi-pendahuluan/img";
mkdirSync(OUT, { recursive: true });

const FONT = 'font-family="Helvetica, Arial, sans-serif"';
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function svg(w, h, body) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">\n` +
    `<rect width="${w}" height="${h}" fill="#ffffff"/>\n${body}</svg>\n`;
}
const text = (x, y, s, { size = 13, anchor = "start", weight = "normal", fill = "#222" } = {}) =>
  `<text x="${x}" y="${y}" ${FONT} font-size="${size}" text-anchor="${anchor}" font-weight="${weight}" fill="${fill}">${esc(s)}</text>\n`;
const rect = (x, y, w, h, fill, stroke = "none", sw = 1) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>\n`;
const line = (x1, y1, x2, y2, stroke = "#222", sw = 1, extra = "") =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${sw}" ${extra}/>\n`;
const circle = (cx, cy, r, fill, stroke = "none") =>
  `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${fill}" stroke="${stroke}"/>\n`;
const ARROW = `<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#222"/></marker></defs>\n`;

/** A pixel grid of nx x ny cells, y down, cell size c, top-left at (ox, oy). */
function grid(ox, oy, nx, ny, c, { labels = true } = {}) {
  let s = "";
  for (let i = 0; i <= nx; i++) s += line(ox + i * c, oy, ox + i * c, oy + ny * c, "#c8c8c8");
  for (let j = 0; j <= ny; j++) s += line(ox, oy + j * c, ox + nx * c, oy + j * c, "#c8c8c8");
  if (labels) {
    for (let i = 0; i < nx; i++) s += text(ox + i * c + c / 2, oy - 5, i, { size: 10, anchor: "middle", fill: "#777" });
    for (let j = 0; j < ny; j++) s += text(ox - 6, oy + j * c + c / 2 + 4, j, { size: 10, anchor: "end", fill: "#777" });
  }
  return s;
}
const cell = (ox, oy, c, x, y, fill) => rect(ox + x * c + 1, oy + y * c + 1, c - 2, c - 2, fill);

// ------------------------------------------------------------ Q1(a) pipeline
function pipeline() {
  const stages = [
    ["1. Application", "scene: posisi vertex, warna, transformasi", "CPU, kode saya"],
    ["2. Vertex processing", "vertex dunia -> vertex layar (pixel)", "programmable (vertex shader)"],
    ["3. Primitive assembly & clipping", "vertex -> garis / segitiga, dipotong ke layar", "fixed"],
    ["4. Rasterisation", "primitif -> fragment (kandidat pixel)", "fixed (raster.mjs di modul ini)"],
    ["5. Fragment shading", "fragment -> warna per fragment", "programmable (fragment shader)"],
    ["6. Per-fragment operations", "warna + depth/alpha/stencil -> lolos atau dibuang", "fixed, bisa dikonfigurasi"],
    ["7. Framebuffer", "grid pixel jadi -> layar atau file", "fixed"],
  ];
  const W = 760, bh = 50, gap = 18, top = 40;
  let s = ARROW + text(W / 2, 24, "Rendering pipeline tujuh tahap", { size: 16, anchor: "middle", weight: "bold" });
  stages.forEach(([name, io, kind], i) => {
    const y = top + i * (bh + gap);
    const prog = kind.startsWith("programmable");
    const mine = name.startsWith("4.");
    s += rect(40, y, 680, bh, prog ? "#fde7cf" : mine ? "#d7ecd9" : "#e3e8f2", "#555", mine ? 2.5 : 1);
    s += text(55, y + 21, name, { weight: "bold" });
    s += text(55, y + 39, io, { size: 12, fill: "#333" });
    s += text(705, y + 21, kind, { size: 11, anchor: "end", fill: "#555" });
    if (i < stages.length - 1) s += line(380, y + bh, 380, y + bh + gap, "#222", 1.5, 'marker-end="url(#arr)"');
  });
  const ly = top + 7 * (bh + gap) + 4;
  s += rect(40, ly, 14, 14, "#fde7cf", "#555") + text(60, ly + 12, "programmable (shader)", { size: 12 });
  s += rect(230, ly, 14, 14, "#e3e8f2", "#555") + text(250, ly + 12, "fixed-function", { size: 12 });
  s += rect(380, ly, 14, 14, "#d7ecd9", "#555", 2.5) + text(400, ly + 12, "tahap yang saya bangun di Modul 2", { size: 12 });
  return svg(W, ly + 30, s);
}

// ------------------------------------------------------ Q1(c) forward/backward
function forwardBackward() {
  const c = 26, nx = 8, ny = 6;
  let s = ARROW;
  // forward: loop over triangles, splat to the pixels each one covers
  const ox = 40, oy = 70;
  s += text(ox, 30, "Forward (object-order): rasterisation", { size: 15, weight: "bold" });
  s += text(ox, 50, "untuk tiap segitiga: cari pixel yang ditutupinya", { size: 12 });
  s += grid(ox, oy, nx, ny, c, { labels: false });
  const T = [[1, 1], [7, 2], [3, 5]];
  triangle({ w: nx, h: ny }, T[0], T[1], T[2], null, {
    onFragment: (x, y) => { s += cell(ox, oy, c, x, y, "#f4b183"); },
  });
  const pts = T.map(([x, y]) => `${ox + x * c},${oy + y * c}`).join(" ");
  s += `<polygon points="${pts}" fill="none" stroke="#c0504d" stroke-width="2"/>\n`;
  s += text(ox, oy + ny * c + 22, "biaya ~ jumlah segitiga x luas pixel-nya", { size: 12, fill: "#444" });

  // backward: loop over pixels, shoot a ray and ask what it hits
  const bx = 420;
  s += text(bx, 30, "Backward (image-order): ray casting", { size: 15, weight: "bold" });
  s += text(bx, 50, "untuk tiap pixel: tembakkan ray, cari hit terdekat", { size: 12 });
  const eye = [bx + 10, oy + 80];
  s += circle(eye[0], eye[1], 6, "#222") + text(eye[0] - 4, eye[1] + 24, "mata", { size: 12 });
  const sx = bx + 150;
  s += line(sx, oy + 20, sx, oy + 140, "#888", 3) + text(sx - 18, oy + 12, "layar", { size: 12 });
  s += circle(bx + 290, oy + 80, 36, "#bdd7ee", "#2f5597") + text(bx + 290, oy + 85, "objek", { size: 12, anchor: "middle" });
  for (let k = 0; k < 6; k++) {
    const py = oy + 30 + k * 20;
    const tx = bx + 340, ty = eye[1] + (py - eye[1]) * ((tx - eye[0]) / (sx - eye[0]));
    s += line(eye[0], eye[1], tx, ty, k === 2 || k === 3 ? "#2f5597" : "#aaa", 1.2, 'marker-end="url(#arr)"');
  }
  s += text(bx, oy + ny * c + 22, "biaya ~ jumlah pixel x biaya uji potong per ray", { size: 12, fill: "#444" });
  return svg(800, oy + ny * c + 40, s);
}

// ---------------------------------------------------- Q2 DDA and Bresenham
function lineFigure() {
  const c = 40, nx = 11, ny = 7, ox = 40, oy = 60;
  let s = text(ox, 24, "Garis (2,1) -> (9,5): pixel Bresenham, y eksak DDA, dan nilai D", { size: 15, weight: "bold" });
  s += text(ox, 44, "y ke bawah. Kotak oranye = pixel yang menyala (DDA dan Bresenham sama persis).", { size: 12 });
  s += grid(ox, oy, nx, ny, c);
  const pts = lineBresenham(2, 1, 9, 5);
  for (const [x, y] of pts) s += cell(ox, oy, c, x, y, "#f4b183");
  // the exact line runs through the pixel centres of its two endpoints
  s += line(ox + 2.5 * c, oy + 1.5 * c, ox + 9.5 * c, oy + 5.5 * c, "#2f5597", 2);
  const dda = lineDDA(2, 1, 9, 5);
  const dx = 7, dy = 4;
  let D = 2 * dy - dx;
  for (let k = 0; k <= dx; k++) {
    const x = 2 + k, yExact = 1 + (k * dy) / dx;
    s += circle(ox + (x + 0.5) * c, oy + (yExact + 0.5) * c, 3.5, "#2f5597");
    s += text(ox + (x + 0.5) * c, oy + ny * c + 18, yExact.toFixed(3), { size: 10, anchor: "middle", fill: "#2f5597" });
    s += text(ox + (x + 0.5) * c, oy + ny * c + 34, k < dx ? `D=${D}` : "", { size: 10, anchor: "middle", fill: "#c0504d" });
    if (dda[k][1] !== pts[k][1]) throw new Error("DDA and Bresenham disagree");
    D += D > 0 ? 2 * (dy - dx) : 2 * dy;
  }
  s += text(ox - 30, oy + ny * c + 18, "y_k", { size: 10, fill: "#2f5597" });
  s += text(ox - 30, oy + ny * c + 34, "D", { size: 10, fill: "#c0504d" });
  return svg(ox * 2 + nx * c, oy + ny * c + 50, s);
}

// ------------------------------------------------------ Q3 triangle E4 signs
function triangleFigure() {
  const c = 48, nx = 8, ny = 8, ox = 40, oy = 60;
  const A = [1, 1], B = [6, 2], C = [3, 7];
  let s = ARROW + text(ox, 24, "Segitiga A(1,1) B(6,2) C(3,7), y ke bawah: tanda tiga edge function", { size: 15, weight: "bold" });
  s += text(ox, 44, "Arsir hijau = pixel yang pusatnya (x+0.5, y+0.5) di dalam (triangle() dengan aturan top-left).", { size: 12 });
  s += grid(ox, oy, nx, ny, c);
  triangle({ w: nx, h: ny }, A, B, C, null, {
    onFragment: (x, y) => { s += cell(ox, oy, c, x, y, "#d7ecd9"); },
  });
  const P = ([x, y]) => [ox + x * c, oy + y * c];
  for (const [U, V] of [[A, B], [B, C], [C, A]]) {
    const [x1, y1] = P(U), [x2, y2] = P(V);
    s += line(x1, y1, x2, y2, "#c0504d", 2, 'marker-end="url(#arr)"');
  }
  for (const [name, V, dx, dy] of [["A", A, -14, -6], ["B", B, 8, -6], ["C", C, -16, 16]]) {
    const [x, y] = P(V);
    s += circle(x, y, 4, "#c0504d") + text(x + dx, y + dy, `${name}(${V})`, { size: 12, weight: "bold", fill: "#c0504d" });
  }
  const E = (Q) => [edge(...A, ...B, ...Q), edge(...B, ...C, ...Q), edge(...C, ...A, ...Q)];
  for (const [name, Q] of [["P1", [3, 3]], ["P2", [5, 5]], ["P3", [1, 4]]]) {
    const [x, y] = P(Q), [eab, ebc, eca] = E(Q);
    const inside = eab >= 0 && ebc >= 0 && eca >= 0;
    s += circle(x, y, 5, inside ? "#2e7d32" : "#555");
    s += text(x + 8, y - 8, `${name}(${Q}): (${eab}, ${ebc}, ${eca}) ${inside ? "di dalam" : "di luar"}`,
      { size: 11, weight: "bold", fill: inside ? "#2e7d32" : "#333" });
  }
  s += text(ox, oy + ny * c + 22, `total = E_AB(C) = ${edge(...A, ...B, ...C)}, luas = ${edge(...A, ...B, ...C) / 2}. Urutan (E_AB, E_BC, E_CA).`, { size: 12 });
  return svg(ox * 2 + nx * c + 120, oy + ny * c + 40, s);
}

// ------------------------------------------------ Q3(d) shared edge, 3 rules
function topLeftFigure() {
  const c = 22, n = 12, T1 = [[2, 2], [8, 2], [8, 8]], T2 = [[2, 2], [8, 8], [2, 8]];
  const panels = [
    ["semua E >= 0", { topLeft: false }],
    ["semua E > 0", { topLeft: false, strictGreater: true }],
    ["rumus top-left modul", { topLeft: true }],
  ];
  let s = text(20, 24, "Dua segitiga berbagi diagonal y = x: tiga cara memutuskan pixel tepat di edge", { size: 15, weight: "bold" });
  panels.forEach(([title, opts], k) => {
    const ox = 30 + k * (n * c + 40), oy = 70;
    const cov = coverage(n, n, [T1, T2], opts);
    const own = new Int8Array(n * n);
    triangle({ w: n, h: n }, ...T1, null, { ...opts, onFragment: (x, y) => { own[y * n + x] |= 1; } });
    triangle({ w: n, h: n }, ...T2, null, { ...opts, onFragment: (x, y) => { own[y * n + x] |= 2; } });
    s += text(ox, 52, `${title}: once=${cov.once} twice=${cov.twice} gaps=${cov.gaps}`, { size: 12, weight: "bold" });
    s += grid(ox, oy, n, n, c, { labels: false });
    for (let y = 0; y < n; y++)
      for (let x = 0; x < n; x++) {
        const k2 = cov.counts[y * n + x];
        if (k2 >= 2) s += cell(ox, oy, c, x, y, "#e53935");
        else if (k2 === 1) s += cell(ox, oy, c, x, y, own[y * n + x] === 1 ? "#f4b183" : "#9dc3e6");
      }
    for (let i = 2; i < 8; i++) if (cov.counts[i * n + i] === 0) s += rect(ox + i * c + 2, oy + i * c + 2, c - 4, c - 4, "none", "#000", 1.5);
    s += line(ox + 2 * c, oy + 2 * c, ox + 8 * c, oy + 8 * c, "#222", 1.2, 'stroke-dasharray="4 3"');
  });
  const ly = 70 + n * c + 20;
  s += rect(30, ly, 14, 14, "#f4b183") + text(50, ly + 12, "segitiga 1", { size: 12 });
  s += rect(140, ly, 14, 14, "#9dc3e6") + text(160, ly + 12, "segitiga 2", { size: 12 });
  s += rect(250, ly, 14, 14, "#e53935") + text(270, ly + 12, "tergambar dua kali", { size: 12 });
  s += rect(410, ly, 14, 14, "none", "#000", 1.5) + text(430, ly + 12, "celah (tidak diisi siapa pun)", { size: 12 });
  return svg(30 + 3 * (n * c + 40), ly + 30, s);
}

// ------------------------------------------ Q4 / E1 sample centre and blit
function sampleCentreFigure() {
  const c = 34, n = 6, oy = 96;
  let s = text(20, 24, "Contoh E1: rectangle 2x2 di sudut integer (1,1) pada framebuffer 6x6", { size: 15, weight: "bold" });
  const panels = [
    ["(a) aturan pusat", "x0 <= x+0.5 < x1", (x, y) => x + 0.5 >= 1 && x + 0.5 < 3 && y + 0.5 >= 1 && y + 0.5 < 3, 0.5],
    ["(b) uji sudut, inklusif", "x0 <= x <= x1", (x, y) => x >= 1 && x <= 3 && y >= 1 && y <= 3, 0],
  ];
  panels.forEach(([title, rule, inside, off], k) => {
    const ox = 30 + k * (n * c + 50);
    s += text(ox, 50, title, { size: 13, weight: "bold" }) + text(ox, 66, rule, { size: 11, fill: "#555" });
    s += grid(ox, oy, n, n, c);
    let lit = 0;
    for (let y = 0; y < n; y++)
      for (let x = 0; x < n; x++) if (inside(x, y)) { s += cell(ox, oy, c, x, y, "#f4b183"); lit++; }
    s += rect(ox + c, oy + c, 2 * c, 2 * c, "none", "#2f5597", 2.5);
    for (let y = 0; y < n; y++)
      for (let x = 0; x < n; x++) s += circle(ox + (x + off) * c, oy + (y + off) * c, 2.5, "#222");
    s += text(ox, oy + n * c + 20, `${lit} pixel menyala`, { size: 12 });
  });
  // (c) a 2x2 texture blitted with no -0.5 offset: each sample sits on a texel corner
  const ox = 30 + 2 * (n * c + 50), tc = 70, ty = oy + 10;
  s += text(ox, 50, "(c) blit bilinear tanpa offset -0.5", { size: 13, weight: "bold" });
  s += text(ox, 66, "sampel jatuh di sudut 4 texel", { size: 11, fill: "#555" });
  const tex = [["#c00000", "#00a000"], ["#0050c0", "#e0b000"]];
  for (let j = 0; j < 2; j++) for (let i = 0; i < 2; i++) s += rect(ox + i * tc, ty + j * tc, tc, tc, tex[j][i], "#fff", 2);
  s += circle(ox + tc, ty + tc, 6, "#fff", "#000");
  s += text(ox, ty + 2 * tc + 22, "bobot tiap texel = 1/4", { size: 12 });
  s += text(ox, ty + 2 * tc + 40, "dengan offset -0.5: sampel di pusat texel,", { size: 12 });
  s += text(ox, ty + 2 * tc + 56, "bobot 1, salinan eksak", { size: 12 });
  s += text(20, oy + n * c + 46, "Garis biru = rectangle [1,3) x [1,3). Titik hitam = posisi sampel yang dipakai aturan itu.", { size: 12 });
  return svg(ox + 2 * tc + 120, oy + n * c + 60, s);
}

const figures = {
  "q1_pipeline.svg": pipeline,
  "q1_forward_backward.svg": forwardBackward,
  "q2_line.svg": lineFigure,
  "q3_triangle.svg": triangleFigure,
  "q3_topleft.svg": topLeftFigure,
  "q4_sample_centre.svg": sampleCentreFigure,
};
for (const [name, fn] of Object.entries(figures)) {
  writeFileSync(join(OUT, name), fn());
  console.log(`wrote ${join(OUT, name)}`);
}
