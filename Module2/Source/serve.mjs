/* Module 2 -- local static server for the viewer, Node built-ins only (no dependency).
 *
 * Replaces the `serve` package (31 Oct 2026: npm audit flagged GHSA-g3hv-75wg-m249 in its
 * minimatch, and npm's fix was a breaking downgrade). Same behaviour the notes rely on:
 *   - serves this folder (Source/), so the viewer at /web/ can fetch ../myplan.json (T5);
 *   - listens on 127.0.0.1 only, never on the network;
 *   - fails loudly if the port is taken instead of moving to a random one (T9);
 *   - never serves anything outside Source/, and a malformed URL gets 403 instead of a crash.
 *
 *   node serve.mjs [--port 4173]        (npm run serve)  ->  http://127.0.0.1:4173/web/
 */
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = resolve(fileURLToPath(new URL(".", import.meta.url)));
export const HOST = "127.0.0.1";
const MIME = {
  ".html": "text/html; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml",
  ".ppm": "image/x-portable-pixmap", ".txt": "text/plain; charset=utf-8",
};

/** Map a URL path to a file inside ROOT, or null if it would leave ROOT or cannot be decoded. */
export function resolvePath(urlPath) {
  let decoded;
  try {
    decoded = decodeURIComponent(urlPath.split("?")[0]);
  } catch {
    return null;  // malformed %-escape: refuse instead of letting the throw stop the server
  }
  const full = resolve(join(ROOT, decoded));
  return full === ROOT || full.startsWith(ROOT + sep) ? full : null;
}

export function makeServer() {
  return createServer(async (req, res) => {
    const url = req.url || "/";
    let path = resolvePath(url);
    if (path === null) {
      res.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" }).end("forbidden\n");
      return;
    }
    try {
      if ((await stat(path)).isDirectory()) {
        if (!url.split("?")[0].endsWith("/")) {          // /web -> /web/ so relative imports resolve
          res.writeHead(301, { Location: url.split("?")[0] + "/" }).end();
          return;
        }
        path = join(path, "index.html");
      }
      const body = await readFile(path);
      res.writeHead(200, { "Content-Type": MIME[extname(path)] || "application/octet-stream" }).end(body);
    } catch {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" }).end(`not found: ${url}\n`);
    }
  });
}

if (process.argv[1] && process.argv[1].endsWith("serve.mjs")) {
  const pi = process.argv.indexOf("--port");
  const port = pi >= 0 ? Number(process.argv[pi + 1]) : 4173;
  const server = makeServer();
  server.on("error", (err) => {
    console.error(`cannot listen on ${HOST}:${port}: ${err.code} (port in use? not switching ports)`);
    process.exit(1);
  });
  server.listen(port, HOST, () => console.log(`serving ${ROOT} at http://${HOST}:${port}/web/  (Ctrl+C to stop)`));
}
