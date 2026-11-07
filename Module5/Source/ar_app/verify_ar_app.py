"""Automated, headless-browser verification of the Pusaka3D AR Explainer.

This is *not* a substitute for testing the actual AR session (WebXR /
Android Scene Viewer / iOS Quick Look) on a real phone -- that handoff to
the OS-level AR viewer cannot be driven from a headless browser and must be
checked on real hardware (see README.md "Known deviations"). What this
script *does* verify, in a real Chromium engine via Playwright, is
everything up to that handoff: the page loads, <model-viewer> parses and
renders the GLB (a real WebGL canvas, not a stub), all hotspots from
hotspots.json are injected at the right slots, clicking one opens the info
panel with the right bilingual text, and the language/quiz-mode controls
work.

Requires: `pip install playwright && python -m playwright install chromium`
(a heavier, optional dependency -- see requirements.txt). Requires the app
to be served over http(s), not opened as a file:// URL (the hotspot fetch()
of hotspots.json needs a real origin) -- start one with
`python -m http.server 8743` from this directory first.

Run: python verify_ar_app.py [base_url]   (default http://localhost:8743)
"""
from __future__ import annotations

import os
import sys

from playwright.sync_api import sync_playwright

URLS = [a for a in sys.argv[1:] if a.startswith("http")]
BASE_URL = URLS[0] if URLS else "http://localhost:8743"
HERE = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(HERE, "screenshots")

_checks = 0


def check(name, condition):
    global _checks
    status = "ok" if condition else "FAIL"
    print(f"[{status}] {name}")
    assert condition, f"failed: {name}"
    _checks += 1


ORBITS = [(float(t), 75.0) for t in range(0, 360, 5)] + [(float(t), 25.0) for t in (0, 90, 180, 270)]


def occlusion_sweep(car=False):
    """Lab 3 no 2 test: turn the camera around the model (the horse, or the car with --car) and
    compare, for every hotspot, what <model-viewer> shows (its opacity) with the geometric truth
    from occlusion.py."""
    import numpy as np
    import occlusion
    tris = occlusion.load_mesh(os.path.join(HERE, "assets", "amr23.glb" if car else "kuda.glb"))
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = browser.new_page(viewport={"width": 390, "height": 800})
        page.goto(f"{BASE_URL}/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_function("document.querySelector('model-viewer').loaded"
                               " && document.querySelectorAll('.hotspot').length === 5", timeout=30000)
        if car:
            page.click("#model-toggle")
            page.wait_for_function("document.querySelector('model-viewer').src.endsWith('assets/amr23.glb')"
                                   " && document.querySelector('model-viewer').loaded", timeout=30000)
        name = "hotspots_amr23.json" if car else "hotspots_kuda.json"
        spots = {h["id"]: h for h in page.evaluate(f"fetch('assets/{name}').then(r => r.json())")["hotspots"]}
        # the idle "interaction prompt" wiggles the camera a few degrees; switch it off for measuring only
        page.evaluate("document.querySelector('model-viewer').interactionPrompt = 'none'")
        for theta, phi in ORBITS:
            state = page.evaluate("""async ([t, p]) => {
                const v = document.querySelector('model-viewer');
                const want = [t * Math.PI / 180, p * Math.PI / 180];
                const off = () => { const o = v.getCameraOrbit();
                    return Math.max(Math.abs(Math.atan2(Math.sin(o.theta - want[0]), Math.cos(o.theta - want[0]))),
                                    Math.abs(o.phi - want[1])); };
                // set the goal, jump, and wait until the camera really sits there (retry if it does not)
                for (let attempt = 0; attempt < 3 && off() > 1e-4; attempt++) {
                    v.cameraOrbit = `${t}deg ${p}deg auto`;
                    await v.updateComplete;
                    v.jumpCameraToGoal();
                    for (let i = 0; i < 100 && off() > 1e-4; i++) await new Promise(r => setTimeout(r, 50));
                }
                // <model-viewer> refreshes hotspot visibility while it renders; give it time to do so
                for (let i = 0; i < 6; i++) await new Promise(r => requestAnimationFrame(r));
                await new Promise(r => setTimeout(r, 300));
                const o = v.getCameraOrbit(), g = v.getCameraTarget();
                return {orbit: [o.theta, o.phi, o.radius], target: [g.x, g.y, g.z], reached: off() <= 1e-4,
                        shown: Object.fromEntries([...document.querySelectorAll('.hotspot')].map(
                            h => [h.slot.replace('hotspot-', ''), parseFloat(getComputedStyle(h).opacity)]))};
            }""", [theta, phi])
            if not state["reached"]:
                raise SystemExit(f"camera did not reach {theta}/{phi} deg; refusing to label a wrong angle")
            cam = occlusion.camera_position(*state["orbit"], state["target"])
            for sid, h in spots.items():
                to_cam = cam - np.array(h["position"])
                facing = float(np.dot(to_cam / np.linalg.norm(to_cam), h["normal"]))  # what <model-viewer> tests
                rows.append((theta, phi, sid, state["shown"][sid] > 0.5,
                             occlusion.is_visible(h["position"], h["normal"], cam, tris), facing))
        docs_img = os.path.join(HERE, "..", "..", "docs", "img")
        shots = () if car else ((255, "occlusion_kaki_255.png"), (70, "occlusion_surai_70.png"))
        for theta, name in shots:
            page.evaluate("""async (t) => { const v = document.querySelector('model-viewer');
                v.cameraOrbit = `${t}deg 75deg auto`; await v.updateComplete; v.jumpCameraToGoal(); }""", theta)
            page.wait_for_timeout(600)
            page.screenshot(path=os.path.join(docs_img, name), clip={"x": 0, "y": 80, "width": 390, "height": 620})
        # is a dimmed hotspot still clickable? (from behind every hotspot is dimmed)
        page.evaluate("""async () => { const v = document.querySelector('model-viewer');
            v.cameraOrbit = '180deg 75deg auto'; await v.updateComplete; v.jumpCameraToGoal(); }""")
        page.wait_for_timeout(400)
        first = f"button[slot='hotspot-{next(iter(spots))}']"
        opacity = page.evaluate(f"parseFloat(getComputedStyle(document.querySelector(\"{first}\")).opacity)")
        page.click(first, force=True)
        page.wait_for_timeout(300)
        clicked = not page.evaluate("document.getElementById('info-panel').hidden")
        browser.close()
    return rows, opacity, clicked


GRAZING = 0.1  # below this the surface is nearly edge-on and a hair of difference flips the answer


def print_occlusion(rows, opacity, clicked):
    ids = list(dict.fromkeys(r[2] for r in rows))
    print("angle  phi   " + "  ".join(f"{i:>6s}" for i in ids) + "    (shown/true: V visible, - hidden, ! wrong)")
    by_angle = {}
    for theta, phi, sid, shown, true, facing in rows:
        by_angle.setdefault((theta, phi), {})[sid] = (shown, true, facing)
    wrong = {i: [] for i in ids}
    for (theta, phi), d in by_angle.items():
        cells = []
        for i in ids:
            shown, true, facing = d[i]
            cells.append(("V" if shown else "-") + ("V" if true else "-") + ("!" if shown != true else " "))
            if shown != true:
                kind = "grazing" if abs(facing) < GRAZING else ("shown but blocked" if shown else "hidden but visible")
                wrong[i].append((theta, phi, f"{kind} ({facing:+.2f})"))
        print(f"{theta:5.0f}  {phi:4.0f}   " + "  ".join(f"{c:>6s}" for c in cells))
    print(f"mismatches per hotspot (in brackets: normal . direction to camera; 'grazing' = |value| < {GRAZING}):")
    for i in ids:
        print(f"  {i:7s} {len(wrong[i]):2d}  " + ", ".join(f"{t:.0f}/{p:.0f} {w}" for t, p, w in wrong[i]))
    print(f"a dimmed hotspot seen from behind: opacity {opacity}, clicking it opens the panel: {clicked}")


def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = browser.new_page(viewport={"width": 390, "height": 800})
        # the quiz picks its target with Math.random; a seeded generator (only in this test, app.js is
        # unchanged) gives the same target, and so the same quiz screenshot, on every run
        page.add_init_script("""
            Math.random = (() => { let s = 12345; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
        """)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.goto(f"{BASE_URL}/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2500)

        mv = page.evaluate("""
            () => {
                const el = document.querySelector('model-viewer');
                return {
                    exists: !!el, loaded: el ? el.loaded : false,
                    modelIsVisible: el ? el.modelIsVisible : false,
                    hasCanvas: !!(el && el.shadowRoot && el.shadowRoot.querySelector('canvas')),
                };
            }
        """)
        check("model-viewer element exists", mv["exists"])
        check("model reported loaded", mv["loaded"])
        check("model reported visible (rendered)", mv["modelIsVisible"])
        check("a real WebGL <canvas> was created inside model-viewer", mv["hasCanvas"])

        src = page.evaluate("document.querySelector('model-viewer').src")
        check(f"the default model is my scanned horse ({src})", src.endswith("assets/kuda.glb"))
        hotspot_count = page.evaluate("document.querySelectorAll('.hotspot').length")
        check(f"5 hotspots injected from hotspots_kuda.json (found {hotspot_count})", hotspot_count == 5)
        check("AR launch button present", page.evaluate("!!document.getElementById('ar-button')"))
        page.evaluate("document.querySelector('model-viewer').interactionPrompt = 'none'")  # steady pictures
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "m5_ar_overview.png"))

        page.click("button[slot='hotspot-surai']")
        page.wait_for_timeout(300)
        title = page.inner_text("#info-title")
        check(f"clicking a hotspot opens the info panel (title='{title}')",
              not page.evaluate("document.getElementById('info-panel').hidden") and len(title) > 0)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "m5_ar_infopanel_en.png"))
        text = page.inner_text("#info-text")

        page.click("#lang-toggle")
        page.wait_for_timeout(300)
        # T11: the module says the toggle swaps every OPEN panel; check it without tapping the hotspot again
        title_now, text_now = page.inner_text("#info-title"), page.inner_text("#info-text")
        check(f"language toggle swaps the panel that is already open ('{title}' -> '{title_now}')",
              title_now != title and text_now != text and title_now == "Surai: 28 foto")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "m5_ar_infopanel_id.png"))
        page.click("button[slot='hotspot-surai']")
        page.wait_for_timeout(300)
        title_id = page.inner_text("#info-title")
        check(f"language toggle changes the panel text ('{title}' -> '{title_id}')", title != title_id)

        page.click("#info-close")
        page.click("#quiz-toggle")
        page.wait_for_timeout(300)
        quiz_target = page.inner_text("#quiz-target")
        check(f"quiz mode picks a target ('{quiz_target}')",
              not page.evaluate("document.getElementById('quiz-banner').hidden") and len(quiz_target) > 0)
        page.click("button[slot='hotspot-alas']")
        page.wait_for_timeout(300)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "m5_ar_quizmode.png"))
        feedback = page.inner_text("#info-text")
        page.click("#lang-toggle")
        page.wait_for_timeout(300)
        feedback_now = page.inner_text("#info-text")
        check("language toggle also swaps the open quiz answer", feedback_now != feedback)
        page.click("#lang-toggle")
        page.click("#info-close")
        page.click("#quiz-toggle")  # quiz off again
        # from behind, every horse hotspot faces away: dimmed by model-viewer, and taps must not reach it
        page.evaluate("""async () => { const v = document.querySelector('model-viewer');
            v.interactionPrompt = 'none'; v.cameraOrbit = '180deg 75deg auto'; await v.updateComplete; v.jumpCameraToGoal(); }""")
        page.wait_for_timeout(800)
        dimmed = page.evaluate("[...document.querySelectorAll('.hotspot')].every(h => !h.hasAttribute('data-visible'))")
        page.click("button[slot='hotspot-alas']", force=True)  # force: click there even though it is not tappable
        page.wait_for_timeout(300)
        check("from behind every hotspot is hidden and tapping one opens nothing",
              dimmed and page.evaluate("document.getElementById('info-panel').hidden"))
        page.evaluate("""async () => { const v = document.querySelector('model-viewer');
            v.cameraOrbit = '0deg 80deg auto'; await v.updateComplete; v.jumpCameraToGoal(); }""")
        page.wait_for_timeout(800)


        page.click("#model-toggle")  # switch to the F1 car
        page.wait_for_function("document.querySelector('model-viewer').src.endsWith('assets/amr23.glb')"
                               " && document.querySelector('model-viewer').loaded"
                               " && document.querySelectorAll('.hotspot').length === 5", timeout=30000)
        page.wait_for_timeout(1500)  # the car's camera is set when its model has loaded
        phi = page.evaluate("document.querySelector('model-viewer').getCameraOrbit().phi * 180 / Math.PI")
        check(f"model switch also moves the camera to the car's own view (polar {phi:.1f} deg, want 75)",
              abs(phi - 75.0) < 0.5)
        page.click("button[slot='hotspot-ban']")
        page.wait_for_timeout(300)
        check(f"model switch loads the car with its own 5 hotspots ('{page.inner_text('#info-title')}')",
              page.evaluate("!!document.querySelector(\"button[slot='hotspot-ban']\")")
              and page.evaluate("document.querySelectorAll(\"button[slot='hotspot-surai']\").length") == 0)
        scales = page.evaluate("document.querySelector('model-viewer').arScale")
        page.click("#model-toggle")  # and back to the horse
        page.wait_for_function("document.querySelector('model-viewer').src.endsWith('assets/kuda.glb')", timeout=15000)
        horse_scale = page.evaluate("document.querySelector('model-viewer').arScale")
        check(f"AR scale: the car may be pinched ({scales}), the horse is fixed at 100% ({horse_scale})",
              scales == "auto" and horse_scale == "fixed")
        check("no uncaught JS errors on the page", len(page_errors) == 0)
        check("no load-error message while every file loads",
              page.evaluate("document.getElementById('load-error').hidden"))

        # a missing file must be said on the page, not only in the console
        for what, pattern in (("hotspot file", "**/hotspots_kuda.json"), ("model", "**/kuda.glb")):
            broken = browser.new_page(viewport={"width": 390, "height": 800})
            broken.route(pattern, lambda route: route.fulfill(status=404, body="not found"))
            broken.goto(f"{BASE_URL}/index.html", wait_until="networkidle", timeout=30000)
            try:
                broken.wait_for_function("!document.getElementById('load-error').hidden", timeout=15000)
            except Exception:
                pass
            message = broken.evaluate("document.getElementById('load-error').hidden ? ''"
                                      " : document.getElementById('load-error').innerText")
            check(f"a missing {what} (404) is said on the page ('{message[:60]}')",
                  pattern.split("/")[-1] in message)
            broken.close()

        browser.close()

    print(f"\nALL CHECKS PASSED ({_checks} ok)")
    print("NOTE: this verifies everything up to the AR launch. The actual WebXR/"
          "Scene Viewer/Quick Look handoff needs a real phone -- see README.md.")


def temple_closeup(out_path):
    """T10 evidence: the course's temple, close up on its finial, written to out_path."""
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = browser.new_page(viewport={"width": 390, "height": 800})
        page.goto(f"{BASE_URL}/index.html", wait_until="networkidle", timeout=30000)
        page.evaluate("document.querySelector('model-viewer').interactionPrompt = 'none'")
        # the temple is no longer offered by the model switch; load its file directly
        page.evaluate("document.querySelector('model-viewer').src = 'assets/pusaka_temple.glb'")
        page.wait_for_function("document.querySelector('model-viewer').src.endsWith('assets/pusaka_temple.glb')"
                               " && document.querySelector('model-viewer').loaded", timeout=15000)
        page.wait_for_timeout(1500)
        page.evaluate("""async () => { const v = document.querySelector('model-viewer');
            v.cameraTarget = '0m 0.36m 0m'; v.cameraOrbit = '35deg 65deg 0.35m';
            await v.updateComplete; v.jumpCameraToGoal(); }""")
        page.wait_for_timeout(1500)
        page.screenshot(path=out_path, clip={"x": 0, "y": 80, "width": 390, "height": 600})
        browser.close()
    print(f"wrote {out_path}")


if __name__ == "__main__" and "--temple-closeup" in sys.argv[1:]:
    temple_closeup(sys.argv[sys.argv.index("--temple-closeup") + 1])
elif __name__ == "__main__" and "--occlusion" in sys.argv[1:]:
    print_occlusion(*occlusion_sweep(car="--car" in sys.argv[1:]))
elif __name__ == "__main__":
    main()
