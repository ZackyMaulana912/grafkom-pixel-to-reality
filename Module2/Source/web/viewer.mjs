/* Module 2 -- the library-side render: my floor plan with Three.js.
 *
 * Draws the SAME plan JSON that raster.mjs draws headless, at the SAME pixel
 * size, with the SAME legend and world -> screen mapping (plan_common.mjs),
 * so `node compare.mjs out/plan_scratch.ppm plan_three.ppm` measures only
 * what the library does differently.
 *
 * The pipeline stages you still own even with a library: vertex winding,
 * canvas SIZE and pixelRatio, where the pixel centre is, and the colour space.
 *
 *   /web/                         -> ../myplan.json
 *   /web/?plan=../pusaka_plan.json -> the module's fallback plan
 */
import * as THREE from "three";
import { legendOf, makeWorldToScreen } from "../plan_common.mjs";

const W = 800, H = 600;
const canvas = document.getElementById("c");

// --- match raster.mjs exactly: no retina scaling, explicit size ---
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.setClearColor(0x121216, 1);

// an orthographic camera in PIXEL space, y-down to match the framebuffer
const camera = new THREE.OrthographicCamera(0, W, 0, H, -10, 10);
const scene = new THREE.Scene();

const hex = ([r, g, b]) => (r << 16) | (g << 8) | b;
let plan, legend, world2screen, group;

function build(fillSilhouette) {
  if (group) scene.remove(group);
  group = new THREE.Group();

  if (fillSilhouette && plan.silhouette) {
    // vertices stay on integer pixel CORNERS: a pixel is filled when its
    // centre is inside, exactly the sample-centre rule of triangle()
    const shape = new THREE.Shape();
    plan.silhouette.points.map(world2screen).forEach(([x, y], i) => {
      i === 0 ? shape.moveTo(x, y) : shape.lineTo(x, y);
    });
    const geo = new THREE.ShapeGeometry(shape);
    // ShapeGeometry fixes the outline's direction itself (isClockWise, then
    // reverse), so its triangles face a normal y-up camera. This camera is
    // y-down, which mirrors the screen: they arrive back-facing and the
    // default FrontSide culls every one. A flat plan has no back: both sides.
    const mat = new THREE.MeshBasicMaterial({ color: 0xe6ecf5, side: THREE.DoubleSide });
    group.add(new THREE.Mesh(geo, mat));
  }

  const colour = Object.fromEntries(legend.map((e) => [e.category, hex(e.rgb)]));
  for (const pl of plan.polylines) {
    // a Bresenham pixel (x, y) is the sample at (x + 0.5, y + 0.5); a GL line
    // through integer coordinates would run on the border between two rows
    const pts = pl.points.map(world2screen).map(([x, y]) => new THREE.Vector3(x + 0.5, y + 0.5, 1));
    if (pl.closed) pts.push(pts[0].clone());
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    const mat = new THREE.LineBasicMaterial({ color: colour[pl.category] ?? 0xffffff });
    group.add(new THREE.Line(geo, mat));
  }
  scene.add(group);
  renderer.render(scene, camera);
}

function buildLegend() {
  const rows = document.getElementById("rows");
  rows.innerHTML = "";
  for (const e of legend) {
    const row = document.createElement("div");
    row.className = "row";
    row.innerHTML =
      `<span class="swatch" style="background:#${hex(e.rgb).toString(16).padStart(6, "0")}"></span>` +
      `<span class="marker">${e.marker}</span><span>${e.label}</span>`;
    rows.appendChild(row);
  }
}

// PPM export so `node compare.mjs` can diff it against the from-scratch raster
function exportPPM() {
  renderer.render(scene, camera);
  const gl = renderer.getContext();
  const px = new Uint8Array(W * H * 4);
  gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px);
  // gl.readPixels is bottom-up; flip to top-down and drop alpha
  const body = new Uint8Array(W * H * 3);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const src = ((H - 1 - y) * W + x) * 4, dst = (y * W + x) * 3;
      body[dst] = px[src]; body[dst + 1] = px[src + 1]; body[dst + 2] = px[src + 2];
    }
  const header = new TextEncoder().encode(`P6\n${W} ${H}\n255\n`);
  const blob = new Blob([header, body], { type: "application/octet-stream" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "plan_three.ppm";
  a.click();
}

function applyFilters() {
  const wrap = document.getElementById("wrap");
  wrap.classList.toggle("cvd-deuteranopia", document.getElementById("cvd").checked);
  wrap.classList.toggle("cvd-protanopia", document.getElementById("cvd2").checked);
  wrap.classList.toggle("cvd-grayscale", document.getElementById("gray").checked);
}

const PLAN_URL = new URLSearchParams(location.search).get("plan") ?? "../myplan.json";
fetch(PLAN_URL)
  .then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then((p) => {
    plan = p;
    legend = legendOf(plan);
    world2screen = makeWorldToScreen(plan, H);
    document.getElementById("plan-name").textContent = plan.name;
    buildLegend();
    build(document.getElementById("fill").checked);
    document.getElementById("fill").addEventListener("change", (e) => build(e.target.checked));
    for (const id of ["cvd", "cvd2", "gray"]) document.getElementById(id).addEventListener("change", applyFilters);
    document.getElementById("export").addEventListener("click", exportPPM);
  })
  .catch((err) => {
    document.getElementById("view").insertAdjacentHTML(
      "beforeend",
      `<p style="color:#f66">Gagal memuat ${PLAN_URL}: ${err}. Jalankan <code>npm run serve</code> dari <code>Module2/Source</code>, lalu buka <code>/web/</code>.</p>`
    );
  });
