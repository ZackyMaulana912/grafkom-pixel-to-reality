/* Module 2 -- PPM -> PNG for the GitHub README (GitHub cannot show .ppm).
 * The encoder is written here with node:zlib only, so no npm package enters
 * the from-scratch side.
 *
 *   node export_png.mjs --src out --out ../docs/img [--scale 1] [names...]
 *   node export_png.mjs --src out --out ../docs/img --scale 8 gap_fixed
 *   node export_png.mjs ... --crop 270,555,50,45 --scale 8 --suffix _zoom diff_plan
 */
import { readdirSync, mkdirSync, writeFileSync } from "node:fs";
import { join, basename } from "node:path";
import { deflateSync } from "node:zlib";
import { Framebuffer } from "./raster.mjs";

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(buf) {
  let c = 0xffffffff;
  for (const b of buf) c = CRC_TABLE[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  out.write(type, 4, "ascii");
  data.copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
  return out;
}

/** 8-bit RGB, non-interlaced PNG; each row gets filter byte 0 (none). */
export function encodePNG(fb) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(fb.w, 0);
  ihdr.writeUInt32BE(fb.h, 4);
  ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  const row = fb.w * 3;
  const raw = Buffer.alloc((row + 1) * fb.h);
  for (let y = 0; y < fb.h; y++) raw.set(fb.data.subarray(y * row, (y + 1) * row), y * (row + 1) + 1);
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw, { level: 9 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

/** a w x h window of fb starting at (x, y) */
function crop(fb, [x, y, w, h]) {
  const c = new Framebuffer(w, h);
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) c.set(i, j, fb.get(x + i, y + j));
  return c;
}

/** nearest-neighbour enlargement so tiny rasters (12x12) stay readable */
function enlarge(fb, k) {
  if (k === 1) return fb;
  const big = new Framebuffer(fb.w * k, fb.h * k);
  for (let y = 0; y < big.h; y++)
    for (let x = 0; x < big.w; x++) big.set(x, y, fb.get((x / k) | 0, (y / k) | 0));
  return big;
}

const opt = (k, d) => { const i = process.argv.indexOf(k); return i >= 0 ? process.argv[i + 1] : d; };
const isMain = process.argv[1] && basename(process.argv[1]) === "export_png.mjs";
if (isMain) {
  const src = opt("--src", "out"), out = opt("--out", "../docs/img"), scale = +opt("--scale", 0);
  const win = opt("--crop", null)?.split(",").map(Number), suffix = opt("--suffix", "");
  const flags = new Set(["--src", "--out", "--scale", "--crop", "--suffix"]);
  const names = process.argv.slice(2).filter((a, i, all) => !a.startsWith("--") && !flags.has(all[i - 1]));
  const files = readdirSync(src).filter((f) => f.endsWith(".ppm") && !f.startsWith("sol_"))
    .filter((f) => names.length === 0 || names.includes(f.replace(/\.ppm$/, "")));
  const missing = names.filter((n) => !files.includes(`${n}.ppm`));
  if (missing.length) console.log(`(!) not found in ${src}/, run the command that makes them first: ${missing.join(", ")}`);
  mkdirSync(out, { recursive: true });
  for (const f of files) {
    const full = Framebuffer.readPPM(join(src, f));
    const fb = win ? crop(full, win) : full;
    // small rasters are enlarged so one pixel is visible; plans stay 1:1
    const k = scale || (fb.w <= 64 ? 16 : 1);
    const png = encodePNG(enlarge(fb, k));
    const dst = join(out, f.replace(/\.ppm$/, `${suffix}.png`));
    writeFileSync(dst, png);
    console.log(`${dst}  ${fb.w}x${fb.h} x${k}  ${png.length} bytes`);
  }
}
