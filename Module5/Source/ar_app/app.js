// Pusaka3D AR Explainer -- Module 5.
// Two models: my scanned horse statue (default) and a downloaded Aston Martin F1 car (CC BY).
// The course's procedural temple stays in assets/ (make_temple_glb.py) but is not offered here.
// Loads the chosen model's hotspot file, injects <model-viewer> hotspot slots, and
// drives the info panel, language toggle, and a simple "quiz mode" that
// turns the hotspots into a tap-the-right-part game. Vanilla JS, no
// framework, no build step -- open index.html (served over http, not
// file://, so the module script and the JSON fetch both work) and it runs.

(function () {
  "use strict";

  const viewer = document.getElementById("viewer");
  const infoPanel = document.getElementById("info-panel");
  const infoTitle = document.getElementById("info-title");
  const infoText = document.getElementById("info-text");
  const infoClose = document.getElementById("info-close");
  const langToggle = document.getElementById("lang-toggle");
  const modelToggle = document.getElementById("model-toggle");
  const quizToggle = document.getElementById("quiz-toggle");
  const quizBanner = document.getElementById("quiz-banner");
  const quizTargetEl = document.getElementById("quiz-target");
  const quizScoreEl = document.getElementById("quiz-score");
  const loadError = document.getElementById("load-error");

  // each model brings its own geometry, camera and hotspot file; the page shell stays the same
  const MODELS = {
    horse: {
      src: "assets/kuda.glb",
      hotspots: "assets/hotspots_kuda.json",
      orbit: "0deg 80deg auto",
      arScale: "fixed",   // always its real 63 cm
      alt: "A rearing horse statue on a long pedestal, scanned from 28 photos, shown at its real size of 63 cm",
    },
    car: {
      src: "assets/amr23.glb",
      hotspots: "assets/hotspots_amr23.json",
      orbit: "30deg 75deg auto",
      arScale: "auto",    // starts at its real 5.3 m; pinch to shrink it into a room
      alt: "An Aston Martin AMR23 Formula 1 car, 5.3 m long, scaled to the FIA tyre size rule",
    },
  };

  let model = "horse";      // "horse" | "car"
  let lang = "en";          // "en" | "id"
  let quizMode = false;
  let hotspots = [];
  let quizTarget = null;
  let quizScore = { correct: 0, attempts: 0 };

  function t(hotspot, field) {
    return hotspot[`${field}_${lang}`];
  }

  // a file that fails to load is said on the page, not only in the console: without this the
  // page kept "Loading the model..." forever, or showed the model with no hotspots and no reason
  const failed = { model: false, hotspots: false };

  function renderLoadError() {
    const { src, hotspots: file } = MODELS[model];
    const parts = [];
    if (failed.model) parts.push(lang === "en" ? `The model ${src} could not be loaded.` : `Model ${src} gagal dimuat.`);
    if (failed.hotspots) {
      parts.push(lang === "en" ? `The info points ${file} could not be loaded.` : `Titik info ${file} gagal dimuat.`);
    }
    if (parts.length) {
      parts.push(lang === "en" ? "Check that the file exists and that the page is opened through a web server (http), not as a file."
                               : "Pastikan filenya ada dan halaman ini dibuka lewat web server (http), bukan sebagai file.");
    }
    loadError.textContent = parts.join(" ");
    loadError.hidden = parts.length === 0;
  }

  viewer.addEventListener("error", () => {
    failed.model = true;
    renderLoadError();
  });
  viewer.addEventListener("load", () => {
    failed.model = false;
    renderLoadError();
  });

  // what the info panel is showing, kept so the language toggle can redraw it (T11):
  // null, { hotspot } for a normal tap, or { hotspot, wanted, correct } for a quiz answer
  let panel = null;

  function renderPanel() {
    if (!panel) return;
    const { hotspot, wanted, correct } = panel;
    if (!wanted) {
      infoTitle.textContent = t(hotspot, "name");
      infoText.textContent = t(hotspot, "text");
    } else if (correct) {
      infoTitle.textContent = `Correct! / Benar!`;
      infoText.textContent = `${t(hotspot, "name")} -- ${t(hotspot, "text")}`;
    } else {
      infoTitle.textContent = `Not quite / Belum tepat`;
      infoText.textContent = lang === "en"
        ? `That was the ${t(hotspot, "name")}. Looking for the ${t(wanted, "name")}.`
        : `Itu adalah ${t(hotspot, "name")}. Yang dicari adalah ${t(wanted, "name")}.`;
    }
    infoPanel.hidden = false;
  }

  function showInfo(hotspot) {
    panel = { hotspot };
    renderPanel();
  }

  function hideInfo() {
    panel = null;
    infoPanel.hidden = true;
  }

  function pickNewQuizTarget() {
    if (hotspots.length === 0) return;
    const others = hotspots.filter((h) => h !== quizTarget);
    quizTarget = others[Math.floor(Math.random() * others.length)] || hotspots[0];
    quizTargetEl.textContent = t(quizTarget, "name");
    quizScoreEl.textContent = `${quizScore.correct}/${quizScore.attempts}`;
  }

  function handleHotspotClick(hotspot) {
    if (!quizMode) {
      showInfo(hotspot);
      return;
    }
    quizScore.attempts += 1;
    const correct = hotspot.id === quizTarget.id;
    if (correct) quizScore.correct += 1;
    panel = { hotspot, wanted: quizTarget, correct };
    renderPanel();
    pickNewQuizTarget();
  }

  function buildHotspotButton(hotspot) {
    const button = document.createElement("button");
    button.slot = `hotspot-${hotspot.id}`;
    button.className = "hotspot";
    button.dataset.position = hotspot.position.join(" ");
    button.dataset.normal = hotspot.normal.join(" ");
    button.textContent = "+";
    // ask <model-viewer> to mark this button with data-visible while its normal faces the camera;
    // without it the button is only dimmed when hidden and can still be tapped (style.css)
    button.dataset.visibilityAttribute = "visible";
    button.setAttribute("aria-label", t(hotspot, "name"));
    button.addEventListener("click", () => handleHotspotClick(hotspot));
    return button;
  }

  function loadHotspots() {
    viewer.querySelectorAll(".hotspot").forEach((el) => el.remove());
    hotspots = [];
    failed.hotspots = false;
    renderLoadError();
    const wanted = model;
    fetch(MODELS[wanted].hotspots)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (wanted !== model) return;  // switched again while this file was loading
        hotspots = data.hotspots;
        hotspots.forEach((hotspot) => {
          viewer.appendChild(buildHotspotButton(hotspot));
        });
        pickNewQuizTarget();
      })
      .catch((err) => {
        console.error(`Could not load ${MODELS[wanted].hotspots}.`, err);
        if (wanted !== model) return;
        failed.hotspots = true;
        renderLoadError();
      });
  }

  langToggle.addEventListener("click", () => {
    lang = lang === "en" ? "id" : "en";
    langToggle.textContent = lang === "en" ? "EN / ID" : "ID / EN";
    if (quizTarget) quizTargetEl.textContent = t(quizTarget, "name");
    hotspots.forEach((h) => {
      const button = viewer.querySelector(`button[slot="hotspot-${h.id}"]`);
      if (button) button.setAttribute("aria-label", t(h, "name"));
    });
    renderPanel();  // the open panel, if any, follows the new language
    renderLoadError();
  });

  modelToggle.addEventListener("click", () => {
    model = model === "horse" ? "car" : "horse";
    modelToggle.textContent = `Model: ${model}`;
    // model-viewer puts the camera back to the camera-orbit attribute when a new model loads,
    // so the new model's camera is set once that load has finished
    viewer.addEventListener("load", () => {
      viewer.cameraOrbit = MODELS[model].orbit;
      viewer.jumpCameraToGoal();
    }, { once: true });
    failed.model = false;
    viewer.src = MODELS[model].src;
    viewer.alt = MODELS[model].alt;
    viewer.arScale = MODELS[model].arScale;
    hideInfo();
    quizScore = { correct: 0, attempts: 0 };
    loadHotspots();
  });

  quizToggle.addEventListener("click", () => {
    quizMode = !quizMode;
    quizToggle.textContent = quizMode ? "Quiz mode: on" : "Quiz mode: off";
    quizToggle.setAttribute("aria-pressed", String(quizMode));
    quizBanner.hidden = !quizMode;
    hideInfo();
    if (quizMode) {
      quizScore = { correct: 0, attempts: 0 };
      pickNewQuizTarget();
    }
  });

  infoClose.addEventListener("click", hideInfo);

  // This script is loaded at the end of <body> without `defer`, so the DOM
  // (including <model-viewer>) is already parsed by the time it runs --
  // call directly rather than waiting for an event that may already have fired.
  loadHotspots();
})();
