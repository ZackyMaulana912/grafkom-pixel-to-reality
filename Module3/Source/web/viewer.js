/* Module 3 -- the real-time renderer: my model in Three.js 0.160.0.
 *
 * Camera, model matrix, light and texture come from the SAME scenes/<name>.json
 * that raster3d.py and raytrace.py read, so compare.py measures how the two
 * renderers differ, not what they were given.
 *
 * Three settings are needed to match raster3d.py (finding T7); each can be
 * switched off from the URL to measure it: ?lights=physical&filter=nearest&texel=gpu
 *   lights  three.js r155+ lights are physical: Lambert is albedo / pi, so the
 *           intensities are multiplied by pi to get raster3d's albedo * cos.
 *   filter  DataTexture defaults to NearestFilter; raster3d is bilinear.
 *   texel   raster3d puts u = 0 and u = 1 on the centres of the edge texels,
 *           a GPU on the texel edges; repeat/offset maps one onto the other.
 */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";

const params = new URLSearchParams(location.search);
const sceneName = params.get("scene") || "mymodel";
const opt = {
  lights: params.get("lights") || "matched",
  filter: params.get("filter") || "linear",
  texel: params.get("texel") || "matched",
};

const canvas = document.getElementById("c");
const status = document.getElementById("status");
const fail = (msg) => {
  status.textContent = msg;
  status.className = "error";
  throw new Error(msg);
};

/** Parse a binary P6 PPM into an sRGB DataTexture (three.js has no PPM loader). */
async function loadPPMTexture(url) {
  const res = await fetch(url);
  if (!res.ok) fail(`texture ${url}: HTTP ${res.status}`);
  const buf = new Uint8Array(await res.arrayBuffer());
  let p = 0;
  const isSpace = (b) => b === 0x20 || b === 0x0a || b === 0x0d || b === 0x09;
  const token = () => {
    while (isSpace(buf[p])) p++;
    let s = "";
    while (!isSpace(buf[p])) s += String.fromCharCode(buf[p++]);
    return s;
  };
  if (token() !== "P6") fail(`${url} is not a binary P6 PPM`);
  const w = +token(), h = +token();
  token();
  p++;                                              // exactly one whitespace after maxval
  const rgba = new Uint8Array(w * h * 4);
  for (let i = 0; i < w * h; i++) {
    rgba.set(buf.subarray(p + i * 3, p + i * 3 + 3), i * 4);
    rgba[i * 4 + 3] = 255;
  }
  const tex = new THREE.DataTexture(rgba, w, h, THREE.RGBAFormat);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.flipY = true;                                 // PPM row 0 is the top; OBJ v = 1 is the top
  if (opt.filter === "linear") tex.magFilter = tex.minFilter = THREE.LinearFilter;
  if (opt.texel === "matched") {
    tex.repeat.set((w - 1) / w, (h - 1) / h);
    tex.offset.set(0.5 / w, 0.5 / h);
  }
  tex.needsUpdate = true;
  return tex;
}

const res = await fetch(`../scenes/${sceneName}.json`);
if (!res.ok) fail(`scene ../scenes/${sceneName}.json: HTTP ${res.status}`);
const sc = await res.json();
const W = sc.frame.w, H = sc.frame.h;

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);                          // 1 canvas pixel = 1 framebuffer pixel
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;   // encode like srgb.linear_to_srgb

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);

const cam = sc.camera;
const camera = new THREE.PerspectiveCamera(cam.fovy_deg, W / H, cam.near, cam.far);
camera.position.set(...cam.eye);
const controls = new OrbitControls(camera, canvas);
controls.target.set(...cam.center);
controls.update();
const home = { pos: camera.position.clone(), target: controls.target.clone() };

const k = opt.lights === "matched" ? Math.PI : 1;
scene.add(new THREE.AmbientLight(0xffffff, sc.light.ambient * k));
const sun = new THREE.DirectionalLight(0xffffff, (1 - sc.light.ambient) * k);
sun.position.set(...sc.light.dir);                  // shines from this direction towards the origin
scene.add(sun);

let model;
try {
  const [obj, tex] = await Promise.all([
    new OBJLoader().loadAsync(`../${sc.model.obj}`),
    loadPPMTexture(`../${sc.model.texture}`),
  ]);
  const mat = new THREE.MeshLambertMaterial({ map: tex, side: THREE.DoubleSide });
  let tris = 0;
  obj.traverse((c) => {
    if (c.isMesh) {
      c.material = mat;
      tris += c.geometry.attributes.position.count / 3;
    }
  });
  obj.position.set(...sc.model.translate);          // M = T Ry S, the same order as scene.py
  obj.rotation.y = THREE.MathUtils.degToRad(sc.model.rot_y_deg);
  obj.scale.set(...sc.model.scale);
  model = obj;
  scene.add(obj);
  status.textContent = `${sc.name}: ${tris} triangles, ${W}x${H}, three.js r${THREE.REVISION}` +
    (opt.lights !== "matched" || opt.filter !== "linear" || opt.texel !== "matched"
      ? `  (comparison mode: lights=${opt.lights} filter=${opt.filter} texel=${opt.texel})` : "");
  document.body.dataset.ready = "1";
} catch (e) {
  fail(`could not load the model or texture (${e.message}). Serve Module3/Source, not web/: ` +
       `python -m http.server 8000 --bind 127.0.0.1, then open /web/`);
}

renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
});

document.getElementById("home").addEventListener("click", () => {
  camera.position.copy(home.pos);
  controls.target.copy(home.target);
  controls.update();
});

document.getElementById("wire").addEventListener("click", () => {
  model?.traverse((c) => { if (c.isMesh) c.material.wireframe = !c.material.wireframe; });
});

/** Read the framebuffer back (bottom row first) and save it as a top-first P6 PPM. */
document.getElementById("export").addEventListener("click", () => {
  renderer.render(scene, camera);
  const gl = renderer.getContext();
  const px = new Uint8Array(W * H * 4);
  gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px);
  const body = new Uint8Array(W * H * 3);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const s = ((H - 1 - y) * W + x) * 4, d = (y * W + x) * 3;
      body[d] = px[s]; body[d + 1] = px[s + 1]; body[d + 2] = px[s + 2];
    }
  const header = new TextEncoder().encode(`P6\n${W} ${H}\n255\n`);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([header, body]));
  a.download = `${sc.name}_three.ppm`;
  a.click();
});
