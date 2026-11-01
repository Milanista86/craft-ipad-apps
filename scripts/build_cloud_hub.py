#!/usr/bin/env python3
"""
Builds and updates the complete 13-app ArtCraft Suite for iPadOS static site (gh-pages).
Downloads the latest web release zips and official 1024x1024 icons from github.com/storytold,
applies iPadOS Home Screen full-bleed icon formatting, Status Bar safe-area offset,
and the floating Touch/Apple Pencil helper, and generates the main hub index.html.
"""

import glob
import gzip
import json
import os
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

APPS = [
    # Creative & Design Suite
    {
        "id": "photocraft",
        "name": "PhotoCraft",
        "prefix": "Photo",
        "suffix": "Craft",
        "role": "Image Editor",
        "category": "Creative & Design",
        "equiv": "Adobe Photoshop Alternative",
        "desc": "Layered raster photo editing, PSD/PSB support, adjustment layers, masks, retouching, and custom brushes.",
        "fallback_bg": (47, 123, 245),
        "color": "#2f7bf5",
        "ink_dark": "#7fb0ff",
        "ink_light": "#1a5bc4",
        "preview": "https://getartcraft.com/images/apps/photocraft/hero.webp",
        "tags": ["PSD / PSB", "RAW", "Adjustment Layers", "Brush Engine"],
    },
    {
        "id": "vectorcraft",
        "name": "VectorCraft",
        "prefix": "Vector",
        "suffix": "Craft",
        "role": "Vector Studio",
        "category": "Creative & Design",
        "equiv": "Adobe Illustrator Alternative",
        "desc": "Precision vector illustration, bezier pen workflows, boolean path operations, multi-artboard layouts, and SVG/PDF export.",
        "fallback_bg": (234, 88, 12),
        "color": "#e8573f",
        "ink_dark": "#ff8a70",
        "ink_light": "#b83a24",
        "preview": "https://getartcraft.com/images/apps/vectorcraft/hero.webp",
        "tags": ["SVG / AI / EPS", "Bezier Pen", "Boolean Ops", "CMYK & Pantone"],
    },
    {
        "id": "designcraft",
        "name": "DesignCraft",
        "prefix": "Design",
        "suffix": "Craft",
        "role": "Page Layout",
        "category": "Creative & Design",
        "equiv": "Adobe InDesign Alternative",
        "desc": "Multi-page desktop publishing, master pages, baseline typography grids, threaded text frames, and print-ready preflight.",
        "fallback_bg": (219, 39, 119),
        "color": "#7bb51c",
        "ink_dark": "#a6e04a",
        "ink_light": "#457008",
        "preview": "https://getartcraft.com/images/apps/designcraft/hero.webp",
        "tags": ["IDML / PDF-X", "Master Pages", "Threaded Text", "CMYK Print"],
    },
    {
        "id": "lightcraft",
        "name": "LightCraft",
        "prefix": "Light",
        "suffix": "Craft",
        "role": "RAW Developer",
        "category": "Creative & Design",
        "equiv": "Adobe Lightroom Alternative",
        "desc": "Non-destructive RAW photo development, film-grade color grading, tone curves, local masking, and catalog management.",
        "fallback_bg": (14, 116, 144),
        "color": "#f2a516",
        "ink_dark": "#ffc14d",
        "ink_light": "#8a5800",
        "preview": "https://getartcraft.com/images/apps/lightcraft/hero.webp",
        "tags": ["CR3 / NEF / ARW", "32-Bit Float", "LUTs & Curves", "Catalog"],
    },
    {
        "id": "filmcraft",
        "name": "FilmCraft",
        "prefix": "Film",
        "suffix": "Craft",
        "role": "Video NLE",
        "category": "Creative & Design",
        "equiv": "Adobe Premiere Pro Alternative",
        "desc": "Nonlinear multi-track video editing, magnetic & ripple timeline trimming, node color grading, and real-time playback.",
        "fallback_bg": (124, 58, 237),
        "color": "#8b5cf6",
        "ink_dark": "#b69cff",
        "ink_light": "#6a3fd6",
        "preview": "https://getartcraft.com/images/apps/filmcraft/color.webp",
        "tags": ["4K / ProRes", "Multi-Track NLE", "Color Wheels", "Audio Mix"],
    },
    {
        "id": "effectcraft",
        "name": "EffectCraft",
        "prefix": "Effect",
        "suffix": "Craft",
        "role": "Motion & VFX",
        "category": "Creative & Design",
        "equiv": "Adobe After Effects Alternative",
        "desc": "Keyframe motion graphics, hybrid layer and node compositing, particle emitters, camera tracking, and procedural VFX.",
        "fallback_bg": (79, 70, 229),
        "color": "#e0368f",
        "ink_dark": "#ff7ab8",
        "ink_light": "#b0206c",
        "preview": "https://getartcraft.com/images/apps/effectcraft/hero.webp",
        "tags": ["Graph Editor", "Node + Layer", "3D Camera", "Particles & Shaders"],
    },
    {
        "id": "figcraft",
        "name": "FigCraft",
        "prefix": "Fig",
        "suffix": "Craft",
        "role": "UI / UX Design",
        "category": "Creative & Design",
        "equiv": "Figma Alternative",
        "desc": "Infinite-canvas interface design, auto-layout frames, variants & design tokens, vector networks, and interactive prototyping.",
        "fallback_bg": (16, 185, 129),
        "color": "#02da96",
        "ink_dark": "#3fe6ae",
        "ink_light": "#017a54",
        "preview": "https://getartcraft.com/images/apps/figcraft/hero.webp",
        "tags": ["Auto-Layout", "Design Tokens", "Prototyping", "Code Inspect"],
    },
    # Office, Audio & Engineering Suite
    {
        "id": "wordcraft",
        "name": "WordCraft",
        "prefix": "Word",
        "suffix": "Craft",
        "role": "Word Processor",
        "category": "Office, Audio & Engineering",
        "equiv": "Microsoft Word Alternative",
        "desc": "Full Ribbon word processor with real-time paginated layout, paragraph styles, track changes, tables, and native DOCX/ODT support.",
        "fallback_bg": (59, 91, 219),
        "color": "#4c6ef5",
        "ink_dark": "#8da2fb",
        "ink_light": "#253e99",
        "preview": "https://getartcraft.com/images/apps/wordcraft/hero.webp",
        "tags": ["DOCX / ODT", "Track Changes", "Citations & TOC", "Print Layout"],
    },
    {
        "id": "gridcraft",
        "name": "GridCraft",
        "prefix": "Grid",
        "suffix": "Craft",
        "role": "Spreadsheet",
        "category": "Office, Audio & Engineering",
        "equiv": "Microsoft Excel Alternative",
        "desc": "High-speed spreadsheet engine with 400+ formulas, pivot tables, financial models, conditional formatting, and XLSX/CSV support.",
        "fallback_bg": (22, 163, 74),
        "color": "#1f9d55",
        "ink_dark": "#5ee089",
        "ink_light": "#136938",
        "preview": "https://getartcraft.com/images/apps/gridcraft/hero.webp",
        "tags": ["XLSX / CSV", "400+ Formulas", "Pivot Tables", "Charts"],
    },
    {
        "id": "deckcraft",
        "name": "DeckCraft",
        "prefix": "Deck",
        "suffix": "Craft",
        "role": "Presentations",
        "category": "Office, Audio & Engineering",
        "equiv": "Microsoft PowerPoint Alternative",
        "desc": "Slide deck authoring, master slide templates, smart object snapping, keyframe transitions, speaker view, and PPTX support.",
        "fallback_bg": (217, 119, 6),
        "color": "#f26b1d",
        "ink_dark": "#ff9657",
        "ink_light": "#ad4306",
        "preview": "https://getartcraft.com/images/apps/deckcraft/hero.webp",
        "tags": ["PPTX / PDF", "Master Slides", "Animations", "Presenter View"],
    },
    {
        "id": "pdfcraft",
        "name": "PdfCraft",
        "prefix": "PDF",
        "suffix": "Craft",
        "role": "PDF Workbench",
        "category": "Office, Audio & Engineering",
        "equiv": "Adobe Acrobat Pro Alternative",
        "desc": "Direct PDF text reflow, page organizer, merger/splitter, OCR recognition, cryptographic redaction, and interactive forms.",
        "fallback_bg": (183, 2, 40),
        "color": "#e8204f",
        "ink_dark": "#f23a62",
        "ink_light": "#b70228",
        "preview": "https://getartcraft.com/images/apps/pdfcraft/hero.webp",
        "tags": ["PDF Edit & OCR", "Merge & Split", "Redaction", "Forms & Sign"],
    },
    {
        "id": "soundcraft",
        "name": "SoundCraft",
        "prefix": "Sound",
        "suffix": "Craft",
        "role": "Digital Audio",
        "category": "Office, Audio & Engineering",
        "equiv": "Avid Pro Tools Alternative",
        "desc": "Digital audio workstation (DAW) for multitrack recording, non-destructive clip editing, piano-roll MIDI, mixing, and mastering.",
        "fallback_bg": (13, 148, 136),
        "color": "#14a9c4",
        "ink_dark": "#52d1ea",
        "ink_light": "#0b6f82",
        "preview": "https://getartcraft.com/images/apps/soundcraft/hero.webp",
        "tags": ["Multitrack DAW", "MIDI & Synths", "FX Rack", "WAV / FLAC"],
    },
    {
        "id": "cadcraft",
        "name": "CADCraft",
        "prefix": "CAD",
        "suffix": "Craft",
        "role": "2D / 3D CAD",
        "category": "Office, Audio & Engineering",
        "equiv": "AutoCAD Alternative",
        "desc": "Precision 2D drafting and parametric 3D solid modeling, geometric constraints, associative dimensioning, and STEP/DXF/DWG workflows.",
        "fallback_bg": (220, 38, 38),
        "color": "#14a3c7",
        "ink_dark": "#4cc7e6",
        "ink_light": "#09596d",
        "preview": "https://getartcraft.com/images/apps/cadcraft/hero.webp",
        "tags": ["DXF / DWG / STEP", "2D Drafting", "3D B-Rep Solids", "Dimensions"],
    },
]
TOUCH_HELPER_SCRIPT = """<script>
(function() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(function(regs) {
      for (let reg of regs) { reg.unregister(); }
    });
    if (window.caches) {
      caches.keys().then(function(keys) {
        for (let k of keys) { caches.delete(k); }
      });
    }
  }
  if (navigator.storage && navigator.storage.persist) {
    navigator.storage.persist().catch(function() {});
  }
  const isIPadDevice = /iPad|Macintosh/i.test(navigator.userAgent) && ('ontouchend' in document);
  async function shareOrDownloadBlob(blob, filename, fallbackFn) {
    const safeName = filename || "document";
    if (isIPadDevice && navigator.canShare && navigator.share) {
      try {
        const file = new File([blob], safeName, { type: blob.type || "application/octet-stream" });
        if (navigator.canShare({ files: [file] })) {
          await navigator.share({ files: [file], title: safeName });
          return;
        }
      } catch (err) {
        if (err && err.name === "AbortError") return;
      }
    }
    if (fallbackFn) fallbackFn();
  }
  const origAnchorClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function() {
    const hasDownload = this.hasAttribute("download") || Boolean(this.download);
    const href = this.href || "";
    const self = this;
    const args = arguments;
    if (isIPadDevice && hasDownload && (href.startsWith("blob:") || href.startsWith("data:"))) {
      const fname = this.getAttribute("download") || this.download || "export";
      fetch(href)
        .then(function(r) { return r.blob(); })
        .then(function(blob) {
          shareOrDownloadBlob(blob, fname, function() { origAnchorClick.apply(self, args); });
        })
        .catch(function() { origAnchorClick.apply(self, args); });
      return;
    }
    return origAnchorClick.apply(this, arguments);
  };
  if (isIPadDevice && !window.showSaveFilePicker) {
    window.showSaveFilePicker = async function(options) {
      const suggestedName = (options && options.suggestedName) ? options.suggestedName : "document";
      return {
        name: suggestedName,
        createWritable: async function() {
          const chunks = [];
          return {
            write: async function(data) {
              chunks.push((data && data.data) ? data.data : data);
            },
            close: async function() {
              const blob = new Blob(chunks);
              await shareOrDownloadBlob(blob, suggestedName);
            }
          };
        }
      };
    };
  }
  window.addEventListener("DOMContentLoaded", function() {
    const isNativeIpa = Boolean(
      (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.craftSaveFile) ||
      window.location.search.indexOf("ipa=1") !== -1
    );
    const statusOffset = isNativeIpa ? "0px" : "18px";
    const style = document.createElement("style");
    style.textContent = `
      :root {
        --ipad-status-offset: ${statusOffset};
      }
      html, body {
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        height: 100% !important;
        overflow: hidden !important;
        background: #1c1c1e !important;
        overscroll-behavior: none !important;
        -webkit-touch-callout: none !important;
        -webkit-user-select: none !important;
        user-select: none !important;
        touch-action: none !important;
      }
      body > canvas, canvas[id] {
        position: fixed !important;
        top: var(--ipad-status-offset) !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100% !important;
        height: calc(100% - var(--ipad-status-offset)) !important;
        display: block !important;
        touch-action: none !important;
      }
      #craft-ipad-helper {
        position: fixed; right: 12px; bottom: 12px; z-index: 2147483647;
        display: flex; align-items: center; gap: 5px;
        background: rgba(24, 24, 28, 0.88);
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 999px; padding: 4px 7px;
        font: 600 12px/1 -apple-system, BlinkMacSystemFont, sans-serif;
        color: #f0f0f5; box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        touch-action: none; user-select: none; -webkit-user-select: none;
      }
      #craft-ipad-helper.collapsed .helper-btn { display: none; }
      #craft-ipad-helper button {
        appearance: none; border: none; background: rgba(255, 255, 255, 0.12);
        color: #f0f0f5; padding: 6px 9px; border-radius: 999px; font: inherit; cursor: pointer;
        white-space: nowrap;
      }
      #craft-ipad-helper button:active { background: rgba(255, 255, 255, 0.24); }
      #craft-ipad-helper button.active { background: #0a84ff; color: #fff; }
      #craft-ipad-toast {
        position: fixed; top: calc(var(--ipad-status-offset) + 34px); left: 50%;
        transform: translateX(-50%); z-index: 2147483647;
        background: rgba(20, 20, 24, 0.88); color: #fff;
        border: 1px solid rgba(255,255,255,0.16); border-radius: 999px;
        padding: 6px 14px; font: 600 12px/1 -apple-system, BlinkMacSystemFont, sans-serif;
        pointer-events: none; opacity: 0; transition: opacity 0.15s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
      }
      #craft-ipad-toast.show { opacity: 1; }
    `;
    document.head.appendChild(style);
    const toast = document.createElement("div");
    toast.id = "craft-ipad-toast";
    document.body.appendChild(toast);
    let toastTimer = null;
    function showToast(text) {
      toast.textContent = text;
      toast.classList.add("show");
      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(function() { toast.classList.remove("show"); }, 650);
    }
    function sendKeyShortcut(key, code, keyCode, ctrlOrCmd, shift) {
      const opts = {
        key: key, code: code, keyCode: keyCode, which: keyCode,
        ctrlKey: Boolean(ctrlOrCmd), metaKey: Boolean(ctrlOrCmd), shiftKey: Boolean(shift),
        bubbles: true, cancelable: true
      };
      const target = document.querySelector("canvas") || window;
      target.dispatchEvent(new KeyboardEvent("keydown", opts));
      window.dispatchEvent(new KeyboardEvent("keydown", opts));
      setTimeout(function() {
        target.dispatchEvent(new KeyboardEvent("keyup", opts));
        window.dispatchEvent(new KeyboardEvent("keyup", opts));
      }, 20);
    }
    let rightClickArmed = false;
    const bar = document.createElement("div");
    bar.id = "craft-ipad-helper";
    bar.className = "collapsed";
    bar.innerHTML = `
      <button id="craft-undo-btn" class="helper-btn" title="Undo (Ctrl+Z)">↩️</button>
      <button id="craft-redo-btn" class="helper-btn" title="Redo (Ctrl+Y)">↪️</button>
      <button id="craft-del-btn" class="helper-btn" title="Delete Selected">⌫</button>
      <button id="craft-rc-btn" class="helper-btn" title="Tap then touch canvas to Right-Click">Right-Click</button>
      <button id="craft-kb-btn" class="helper-btn" title="Open On-Screen Keyboard">⌨️</button>
      <button id="craft-reload-btn" class="helper-btn" title="Reload / Fetch Latest Update">🔄</button>
      <button id="craft-toggle-btn" title="Tap to open tools, or drag to move">⚙️</button>
    `;
    document.body.appendChild(bar);
    try {
      const savedPos = JSON.parse(localStorage.getItem("craft_helper_pos") || "null");
      if (savedPos && typeof savedPos.left === "number" && typeof savedPos.top === "number") {
        const maxLeft = Math.max(8, window.innerWidth - 60);
        const maxTop = Math.max(24, window.innerHeight - 48);
        bar.style.left = Math.min(Math.max(8, savedPos.left), maxLeft) + "px";
        bar.style.top = Math.min(Math.max(24, savedPos.top), maxTop) + "px";
        bar.style.right = "auto";
        bar.style.bottom = "auto";
      }
    } catch (e) {}
    const undoBtn = document.getElementById("craft-undo-btn");
    const redoBtn = document.getElementById("craft-redo-btn");
    const delBtn = document.getElementById("craft-del-btn");
    const rcBtn = document.getElementById("craft-rc-btn");
    const kbBtn = document.getElementById("craft-kb-btn");
    const reloadBtn = document.getElementById("craft-reload-btn");
    const toggleBtn = document.getElementById("craft-toggle-btn");
    // Draggable + Tappable toggle button
    let dragStart = null;
    let didDragPill = false;
    toggleBtn.addEventListener("pointerdown", function(e) {
      e.stopPropagation();
      toggleBtn.setPointerCapture(e.pointerId);
      const rect = bar.getBoundingClientRect();
      dragStart = { x: e.clientX, y: e.clientY, left: rect.left, top: rect.top };
      didDragPill = false;
    });
    toggleBtn.addEventListener("pointermove", function(e) {
      if (!dragStart) return;
      const dx = e.clientX - dragStart.x;
      const dy = e.clientY - dragStart.y;
      if (Math.hypot(dx, dy) > 6) {
        didDragPill = true;
        const rect = bar.getBoundingClientRect();
        const newLeft = Math.min(Math.max(6, dragStart.left + dx), window.innerWidth - rect.width - 6);
        const newTop = Math.min(Math.max(20, dragStart.top + dy), window.innerHeight - rect.height - 6);
        bar.style.left = newLeft + "px";
        bar.style.top = newTop + "px";
        bar.style.right = "auto";
        bar.style.bottom = "auto";
      }
    });
    toggleBtn.addEventListener("pointerup", function(e) {
      if (!dragStart) return;
      e.stopPropagation();
      if (didDragPill) {
        try {
          const rect = bar.getBoundingClientRect();
          localStorage.setItem("craft_helper_pos", JSON.stringify({ left: rect.left, top: rect.top }));
        } catch (err) {}
      } else {
        bar.classList.toggle("collapsed");
      }
      dragStart = null;
      didDragPill = false;
    });
    undoBtn.addEventListener("pointerdown", function(e) {
      e.stopPropagation();
      sendKeyShortcut("z", "KeyZ", 90, true, false);
      showToast("↩️ Undo");
    });
    redoBtn.addEventListener("pointerdown", function(e) {
      e.stopPropagation();
      sendKeyShortcut("y", "KeyY", 89, true, false);
      showToast("↪️ Redo");
    });
    delBtn.addEventListener("pointerdown", function(e) {
      e.stopPropagation();
      sendKeyShortcut("Delete", "Delete", 46, false, false);
      sendKeyShortcut("Backspace", "Backspace", 8, false, false);
    });
    rcBtn.addEventListener("pointerdown", function(e) {
      e.stopPropagation();
      rightClickArmed = !rightClickArmed;
      rcBtn.classList.toggle("active", rightClickArmed);
      if (rightClickArmed) showToast("Tap canvas to Right-Click");
    });
    kbBtn.addEventListener("pointerdown", function(e) {
      e.stopPropagation();
      let input = document.querySelector("input, textarea");
      if (!input) {
        input = document.createElement("input");
        input.type = "text";
        input.style.cssText = "position:fixed;opacity:0;pointer-events:none;left:0;top:0;width:1px;height:1px;";
        document.body.appendChild(input);
      }
      input.focus();
    });
    reloadBtn.addEventListener("pointerdown", function(e) {
      e.stopPropagation();
      window.location.replace(window.location.pathname + "?v=" + Date.now());
    });
    window.addEventListener("pointerdown", function(e) {
      if (!rightClickArmed || bar.contains(e.target)) return;
      rightClickArmed = false;
      rcBtn.classList.remove("active");
      e.stopImmediatePropagation();
      e.preventDefault();
      const opts = {
        bubbles: true, cancelable: true,
        clientX: e.clientX, clientY: e.clientY,
        screenX: e.screenX, screenY: e.screenY,
        button: 2, buttons: 2
      };
      e.target.dispatchEvent(new PointerEvent("pointerdown", opts));
      e.target.dispatchEvent(new MouseEvent("mousedown", opts));
      e.target.dispatchEvent(new MouseEvent("contextmenu", opts));
      e.target.dispatchEvent(new PointerEvent("pointerup", { ...opts, buttons: 0 }));
      e.target.dispatchEvent(new MouseEvent("mouseup", { ...opts, buttons: 0 }));
    }, true);
    // Passive multi-finger touch gestures (2-finger tap = Undo, 3-finger tap = Redo, 2-finger pinch = Zoom)
    // Never intercepts mouse, trackpad, keyboard, Apple Pencil, or 1-finger touch events
    let touchState = null;
    window.addEventListener("touchstart", function(e) {
      if (bar.contains(e.target)) return;
      const count = e.touches.length;
      if (count >= 2) {
        const pts = [];
        for (let i = 0; i < count; i++) {
          pts.push({ x: e.touches[i].clientX, y: e.touches[i].clientY });
        }
        const dist = count === 2 ? Math.hypot(pts[1].x - pts[0].x, pts[1].y - pts[0].y) : 0;
        touchState = {
          maxFingers: Math.max(touchState ? touchState.maxFingers : 0, count),
          startTime: touchState ? touchState.startTime : Date.now(),
          startPts: pts,
          lastDist: dist,
          maxMove: touchState ? touchState.maxMove : 0
        };
      }
    }, { passive: true });
    window.addEventListener("touchmove", function(e) {
      if (!touchState) return;
      const count = e.touches.length;
      if (count >= 2 && touchState.startPts.length >= 2) {
        const dx0 = e.touches[0].clientX - touchState.startPts[0].x;
        const dy0 = e.touches[0].clientY - touchState.startPts[0].y;
        touchState.maxMove = Math.max(touchState.maxMove, Math.hypot(dx0, dy0));
        if (count === 2) {
          const x0 = e.touches[0].clientX, y0 = e.touches[0].clientY;
          const x1 = e.touches[1].clientX, y1 = e.touches[1].clientY;
          const newDist = Math.hypot(x1 - x0, y1 - y0);
          const deltaDist = touchState.lastDist - newDist;
          if (Math.abs(deltaDist) > 3 && touchState.maxMove > 12) {
            const canvas = document.querySelector("canvas");
            if (canvas) {
              canvas.dispatchEvent(new WheelEvent("wheel", {
                deltaY: deltaDist * 1.4,
                ctrlKey: true,
                metaKey: true,
                clientX: (x0 + x1) / 2,
                clientY: (y0 + y1) / 2,
                bubbles: true,
                cancelable: true
              }));
            }
            touchState.lastDist = newDist;
          }
        }
      }
    }, { passive: true });
    window.addEventListener("touchend", function(e) {
      if (!touchState) return;
      if (e.touches.length === 0) {
        const elapsed = Date.now() - touchState.startTime;
        if (elapsed < 260 && touchState.maxMove < 14) {
          if (touchState.maxFingers === 2) {
            sendKeyShortcut("z", "KeyZ", 90, true, false);
            showToast("↩️ Undo");
          } else if (touchState.maxFingers === 3) {
            sendKeyShortcut("y", "KeyY", 89, true, false);
            showToast("↪️ Redo");
          }
        }
        touchState = null;
      }
    }, { passive: true });
    window.addEventListener("touchcancel", function() {
      touchState = null;
    }, { passive: true });
  });
})();
</script>"""
def make_full_bleed_icons(src_png: Path, out_dir: Path, fallback_rgb):
    from PIL import Image
    img = Image.open(src_png).convert("RGBA")
    w, h = img.size
    pixels = img.load()
    min_x, min_y, max_x, max_y = w, h, 0, 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if pixels[x, y][3] > 200:
                if x < min_x: min_x = x
                if y < min_y: min_y = y
                if x > max_x: max_x = x
                if y > max_y: max_y = y
    if max_x <= min_x or max_y <= min_y:
        min_x, min_y, max_x, max_y = 0, 0, w - 1, h - 1
    sample_y = min(h - 1, min_y + 25)
    sample_px = pixels[w // 2, sample_y]
    bg_rgb = (sample_px[0], sample_px[1], sample_px[2]) if sample_px[3] > 200 else fallback_rgb
    cropped = img.crop((min_x, min_y, max_x + 1, max_y + 1))
    for size, names in [(512, ["icon.png"]), (180, ["apple-touch-icon.png", "apple-touch-icon-precomposed.png"])]:
        bg = Image.new("RGBA", (size, size), (*bg_rgb, 255))
        resized = cropped.resize((size, size), Image.Resampling.LANCZOS)
        bg.alpha_composite(resized)
        final_img = bg.convert("RGB")
        for fname in names:
            final_img.save(out_dir / fname, format="PNG", optimize=True)
    return "#{:02x}{:02x}{:02x}".format(*bg_rgb)
def build_direct_or_multipart_html(app_id: str, app_name: str, app_dir: Path):
    app_sub = app_dir / "app"
    if not app_sub.is_dir():
        return
    # Always copy snippets into app/snippets if both exist
    if (app_dir / "snippets").is_dir():
        shutil.copytree(app_dir / "snippets", app_sub / "snippets", dirs_exist_ok=True)
    parts = sorted(app_sub.glob("*.part-*"))
    js_files = list(app_sub.glob("*-web.js"))
    if not parts or not js_files:
        return
    js_name = js_files[0].name
    shutil.copy2(js_files[0], app_dir / js_name)
    # Decompress parts into a temporary file to check total uncompressed Wasm size
    tmp_wasm = Path(f"/tmp/{app_id}_full.wasm")
    with open(tmp_wasm, "wb") as out_f:
        cat_proc = subprocess.Popen(["cat"] + [str(p) for p in parts], stdout=subprocess.PIPE)
        gunzip_proc = subprocess.Popen(["gzip", "-dc"], stdin=cat_proc.stdout, stdout=out_f)
        cat_proc.stdout.close()
        gunzip_proc.communicate()
    wasm_size = tmp_wasm.stat().st_size if tmp_wasm.exists() else 0
    print(f"  [{app_id}] Decompressed Wasm size: {wasm_size / (1024*1024):.2f} MB")
    # GitHub has a 100 MB per-file limit. If < 90 MB, use a single direct .wasm file for fast streaming.
    if 0 < wasm_size < 90 * 1024 * 1024:
        wasm_filename = f"{app_id}-web_bg.wasm"
        shutil.move(str(tmp_wasm), str(app_dir / wasm_filename))
        shutil.rmtree(app_sub, ignore_errors=True)
        for boot_f in app_dir.glob("*-web-boot*"):
            boot_f.unlink(missing_ok=True)
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>{app_name}</title>
  <script type="module">
    import init, * as bindings from './{js_name}';
    try {{
      const wasm = await init({{ module_or_path: './{wasm_filename}' }});
      window.wasmBindings = bindings;
      const loading = document.getElementById('{app_id}_loading');
      if (loading) loading.remove();
      dispatchEvent(new CustomEvent("TrunkApplicationStarted", {{detail: {{wasm}}}}));
    }} catch (err) {{
      console.error("{app_name} init error:", err);
      const loading = document.getElementById('{app_id}_loading');
      if (loading) loading.textContent = "Error starting {app_name}: " + err;
    }}
  </script>
  <style>
    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #1c1c1e; }}
    #{app_id}_canvas {{ position: absolute; inset: 0; width: 100%; height: 100%; display: block; }}
    #{app_id}_loading {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
      padding: 0 16px; text-align: center; color: #b8b8b8; font: 14px system-ui, sans-serif; pointer-events: none; }}
  </style>
</head>
<body>
  <canvas id="{app_id}_canvas"></canvas>
  <div id="{app_id}_loading"><p>Loading {app_name}&hellip;</p></div>
</body>
</html>
"""
        (app_dir / "index.html").write_text(index_html, encoding="utf-8")
    else:
        # Keep <20 MB .part-* files for >= 90 MB Wasm apps (e.g., LightCraft) and assemble in browser
        tmp_wasm.unlink(missing_ok=True)
        for boot_f in app_dir.glob("*-web-boot*"):
            boot_f.unlink(missing_ok=True)
        part_urls = [f"./app/{p.name}" for p in parts]
        part_urls_json = json.dumps(part_urls)
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>{app_name}</title>
  <script type="module">
    import init, * as bindings from './{js_name}';
    const PART_URLS = {part_urls_json};
    try {{
      const loadingEl = document.getElementById('{app_id}_loading');
      const chunks = [];
      let totalLen = 0;
      for (let i = 0; i < PART_URLS.length; i++) {{
        if (loadingEl) loadingEl.textContent = `Downloading {app_name} (part ${{i+1}} of ${{PART_URLS.length}})…`;
        const r = await fetch(PART_URLS[i]);
        if (!r.ok) throw new Error(`HTTP ${{r.status}} fetching ${{PART_URLS[i]}}`);
        const buf = new Uint8Array(await r.arrayBuffer());
        chunks.push(buf);
        totalLen += buf.byteLength;
      }}
      if (loadingEl) loadingEl.textContent = `Starting {app_name}…`;
      const compressed = new Uint8Array(totalLen);
      let offset = 0;
      for (const c of chunks) {{ compressed.set(c, offset); offset += c.byteLength; }}
      const ds = new DecompressionStream('gzip');
      const decompressedStream = new Blob([compressed]).stream().pipeThrough(ds);
      const wasmBytes = await new Response(decompressedStream).arrayBuffer();
      const wasm = await init({{ module_or_path: wasmBytes }});
      window.wasmBindings = bindings;
      if (loadingEl) loadingEl.remove();
      dispatchEvent(new CustomEvent("TrunkApplicationStarted", {{detail: {{wasm}}}}));
    }} catch (err) {{
      console.error("{app_name} init error:", err);
      const loading = document.getElementById('{app_id}_loading');
      if (loading) loading.textContent = "Error starting {app_name}: " + err;
    }}
  </script>
  <style>
    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #1c1c1e; }}
    #{app_id}_canvas {{ position: absolute; inset: 0; width: 100%; height: 100%; display: block; }}
    #{app_id}_loading {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
      padding: 0 16px; text-align: center; color: #b8b8b8; font: 14px system-ui, sans-serif; pointer-events: none; }}
  </style>
</head>
<body>
  <canvas id="{app_id}_canvas"></canvas>
  <div id="{app_id}_loading"><p>Loading {app_name}&hellip;</p></div>
</body>
</html>
"""
        (app_dir / "index.html").write_text(index_html, encoding="utf-8")
def process_app(app_meta: dict, out_root: Path):
    app_id = app_meta["id"]
    app_name = app_meta["name"]
    repo = f"storytold/{app_id}"
    print(f"=== Processing {app_name} ({repo}) ===")
    app_dir = out_root / app_id
    shutil.rmtree(app_dir, ignore_errors=True)
    app_dir.mkdir(parents=True, exist_ok=True)
    # 1. Download latest *-web-*.zip release
    res = subprocess.run(
        ["gh", "release", "view", "--repo", repo, "--json", "assets", "--jq", ".assets[].name"],
        capture_output=True, text=True, check=True
    )
    assets = [line.strip() for line in res.stdout.splitlines() if re.search(r"web.*\.zip$", line, re.I)]
    if not assets:
        raise RuntimeError(f"No web zip asset found for {repo}")
    asset_name = assets[0]
    print(f"  Downloading {asset_name}...")
    dl_dir = Path(f"/tmp/{app_id}-dl")
    ext_dir = Path(f"/tmp/{app_id}-ext")
    shutil.rmtree(dl_dir, ignore_errors=True)
    shutil.rmtree(ext_dir, ignore_errors=True)
    dl_dir.mkdir(parents=True)
    ext_dir.mkdir(parents=True)
    subprocess.run(["gh", "release", "download", "--repo", repo, "--pattern", asset_name, "--dir", str(dl_dir)], check=True)
    subprocess.run(["unzip", "-q", str(dl_dir / asset_name), "-d", str(ext_dir)], check=True)
    index_files = list(ext_dir.rglob("index.html"))
    if not index_files:
        raise RuntimeError(f"No index.html inside {asset_name}")
    bundle_dir = index_files[0].parent
    for item in bundle_dir.iterdir():
        if item.name in {".htaccess", "_headers", "HOSTING.md", "README.md", "ATTRIBUTION.md", "NOTICE"} or item.name.startswith("LICENSE") or item.suffix == ".ico":
            continue
        dest = app_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
    shutil.rmtree(dl_dir, ignore_errors=True)
    shutil.rmtree(ext_dir, ignore_errors=True)
    # 2. Download official 1024x1024 icon and format edge-to-edge for iPadOS
    icon_url = f"https://raw.githubusercontent.com/storytold/{app_id}/main/assets/app-icon/{app_id}-1024.png"
    raw_icon = Path(f"/tmp/{app_id}-1024.png")
    urllib.request.urlretrieve(icon_url, str(raw_icon))
    bg_hex = make_full_bleed_icons(raw_icon, app_dir, app_meta["fallback_bg"])
    raw_icon.unlink(missing_ok=True)
    # 3. Unpack single-part Wasm or configure multi-part Wasm loader
    build_direct_or_multipart_html(app_id, app_name, app_dir)
    # 4. Write manifest.json
    manifest = {
        "name": app_name,
        "short_name": app_name,
        "description": app_meta["desc"],
        "start_url": "./?v=4",
        "scope": "./",
        "display": "standalone",
        "orientation": "any",
        "background_color": bg_hex,
        "theme_color": "#1c1c1e",
        "icons": [
            {"src": "./apple-touch-icon.png?v=4", "sizes": "180x180", "type": "image/png"},
            {"src": "./icon.png?v=4", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    (app_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # 5. Patch index.html with iPad PWA headers + Status Bar safe-area offset + Touch Helper
    index_path = app_dir / "index.html"
    html = index_path.read_text(encoding="utf-8")
    html = re.sub(r'\s+integrity="[^"]+"', "", html)
    html = re.sub(r'<link rel="icon"[^>]+>', "", html)
    html = re.sub(r'<link rel="preload"[^>]+type="application/wasm"[^>]*>', "", html)
    pwa_head = f"""
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black">
  <meta name="apple-mobile-web-app-title" content="{app_name}">
  <link rel="apple-touch-icon" sizes="180x180" href="./apple-touch-icon.png?v=4">
  <link rel="apple-touch-icon" sizes="512x512" href="./icon.png?v=4">
  <link rel="icon" type="image/png" sizes="180x180" href="./apple-touch-icon.png?v=4">
  <link rel="manifest" href="./manifest.json?v=4">"""
    html = re.sub(r"(<title>[^<]+</title>)", r"\1" + pwa_head, html, count=1)
    html = html.replace("</head>", TOUCH_HELPER_SCRIPT + "\n</head>")
    index_path.write_text(html, encoding="utf-8")


def generate_hub_index(out_root: Path):
    dock_items = []
    lineup_cards = []
    footer_app_links = []
    for idx, app in enumerate(APPS, start=1):
        num_str = f"{idx:02d}"
        cat_slug = "creative" if app["category"] == "Creative & Design" else "office"
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in app["tags"])
        search_blob = f"{app['name']} {app['role']} {app['equiv']} {app['desc']} {' '.join(app['tags'])}".lower()
        dock_items.append(f"""              <a href="#app-{app['id']}" class="dock-item" data-cat="{cat_slug}" style="--app: {app['color']}; --app-dark: {app['ink_dark']}; --app-light: {app['ink_light']};" title="Jump to {app['name']} ({app['equiv']})">
                <div class="dock-icon-wrap">
                  <img src="./{app['id']}/icon.png?v=4" alt="{app['name']}" loading="lazy">
                </div>
                <span class="dock-label">{app['prefix']}<em class="dock-craft">{app['suffix']}</em></span>
              </a>""")
        lineup_cards.append(f"""          <article id="app-{app['id']}" class="app-card" data-cat="{cat_slug}" data-search="{search_blob}" style="--app: {app['color']}; --app-dark: {app['ink_dark']}; --app-light: {app['ink_light']};">
            <div class="card-accent-bar"></div>
            <div class="card-hud">
              <div class="card-hud-left">
                <span class="num-badge">{num_str}</span>
                <span class="hud-label card-role">{app['role']}</span>
              </div>
              <span class="hud-label card-equiv">{app['equiv']}</span>
            </div>
            <a href="./{app['id']}/?v=4" class="card-preview" aria-label="Launch {app['name']}">
              <img src="{app['preview']}" alt="{app['name']} workspace preview" loading="lazy" onerror="this.style.display='none'">
              <div class="preview-pill">LIVE IPADOS WEBASM</div>
            </a>
            <div class="card-body">
              <div class="card-title-row">
                <div class="card-icon-float">
                  <img src="./{app['id']}/icon.png?v=4" alt="{app['name']} icon" loading="lazy">
                </div>
                <div class="card-title-group">
                  <h3 class="card-title">
                    <a href="./{app['id']}/?v=4">{app['prefix']}<span class="craft-accent">{app['suffix']}</span></a>
                  </h3>
                  <div class="card-cat-sub">{app['category']}</div>
                </div>
                <a href="./{app['id']}/?v=4" class="card-quick-arrow" title="Launch {app['name']}">↗</a>
              </div>
              <p class="card-desc">{app['desc']}</p>
              <div class="card-tags">
                {tags_html}
              </div>
              <div class="card-actions">
                <a class="btn-launch" href="./{app['id']}/?v=4">
                  <span>Launch {app['name']}</span>
                  <span class="arrow">↗</span>
                </a>
                <a class="btn-sub" href="https://github.com/Milanista86/craft-ipad-apps/releases/download/v1.0.0/{app['name']}-iPad.ipa" title="Download Native iPadOS .ipa Installer">
                  ↓ .IPA
                </a>
                <a class="btn-sub" href="https://github.com/storytold/{app['id']}" target="_blank" rel="noopener noreferrer" title="View Upstream Rust Source on GitHub">
                  SRC ↗
                </a>
              </div>
            </div>
          </article>""")
        footer_app_links.append(
            f'            <a href="./{app["id"]}/?v=4" class="footer-link">{app["name"]} <span>({app["role"]})</span></a>'
        )
    dock_html = "\n".join(dock_items)
    lineup_html = "\n".join(lineup_cards)
    footer_apps_html = "\n".join(footer_app_links)
    hub_html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
  <title>ArtCraft Suite for iPadOS — Thirteen Apps. One Craft.</title>
  <meta name="description" content="Run all 13 open-source desktop creative, office, audio, and CAD apps by ArtCraft (@storytold) natively on iPadOS — with full Mouse, Trackpad, Keyboard, and Apple Pencil support.">
  <meta property="og:title" content="ArtCraft Suite for iPadOS — Thirteen Apps. One Craft.">
  <meta property="og:description" content="Photoshop, Illustrator, InDesign, Lightroom, Premiere, After Effects, Figma, Word, Excel, PowerPoint, Acrobat, Pro Tools & AutoCAD alternatives built in Rust for iPadOS.">
  <meta property="og:type" content="website">
  <link rel="icon" type="image/png" href="./photocraft/apple-touch-icon.png?v=4">
  <link rel="apple-touch-icon" href="./photocraft/apple-touch-icon.png?v=4">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@118,500..800&family=Geist+Mono:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script>
    (function() {{
      try {{
        var saved = localStorage.getItem('artcraft_ipad_theme');
        if (saved === 'light' || saved === 'dark') {{
          document.documentElement.setAttribute('data-theme', saved);
        }}
      }} catch (e) {{}}
    }})();
  </script>
  <style>
    :root {{
      --bg: #f2f1ee;
      --bg-raised: #faf9f7;
      --bg-sunken: #e9e8e4;
      --bg-glass: rgba(242, 241, 238, 0.86);
      --ink: #101014;
      --ink-strong: #000000;
      --muted: rgba(16, 16, 20, 0.64);
      --faint: rgba(16, 16, 20, 0.42);
      --line: rgba(16, 16, 20, 0.16);
      --line-strong: rgba(16, 16, 20, 0.42);
      --accent: #2d81ff;
      --accent-ink: #1659c4;
      --invert-bg: #101014;
      --invert-fg: #f2f1ee;
      --emerald: #10b981;
      --font-display: 'Archivo', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-serif: 'Instrument Serif', Georgia, serif;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
      color-scheme: light;
    }}
    :root[data-theme="dark"] {{
      --bg: #121316;
      --bg-raised: #101014;
      --bg-sunken: #08090b;
      --bg-glass: rgba(18, 19, 22, 0.86);
      --ink: #f2f1ee;
      --ink-strong: #ffffff;
      --muted: rgba(242, 241, 238, 0.62);
      --faint: rgba(242, 241, 238, 0.38);
      --line: rgba(242, 241, 238, 0.14);
      --line-strong: rgba(242, 241, 238, 0.38);
      --accent: #2d81ff;
      --accent-ink: #74aaff;
      --invert-bg: #ffffff;
      --invert-fg: #0b0b0c;
      --emerald: #34d399;
      color-scheme: dark;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    html {{
      scroll-behavior: smooth;
      background: var(--bg);
      color: var(--ink);
      font-family: var(--font-sans);
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}
    body {{
      background: var(--bg);
      color: var(--ink);
      min-height: 100vh;
      overflow-x: hidden;
    }}
    a {{
      color: inherit;
      text-decoration: none;
    }}
    /* Typography Helpers */
    .font-display {{
      font-family: var(--font-display);
      font-weight: 650;
      font-stretch: 118%;
      letter-spacing: -0.035em;
      line-height: 1.02;
      font-variation-settings: "wdth" 118;
    }}
    .font-serif {{
      font-family: var(--font-serif);
      font-weight: 400;
      font-style: italic;
      letter-spacing: -0.01em;
    }}
    .hud-label {{
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--muted);
    }}
    /* Corner Crosshair Ticks */
    .tick {{
      position: absolute;
      width: 7px;
      height: 7px;
      pointer-events: none;
      z-index: 2;
    }}
    .tick-tl {{ top: -1px; left: -1px; border-top: 1.5px solid var(--ink-strong); border-left: 1.5px solid var(--ink-strong); }}
    .tick-tr {{ top: -1px; right: -1px; border-top: 1.5px solid var(--ink-strong); border-right: 1.5px solid var(--ink-strong); }}
    .tick-bl {{ bottom: -1px; left: -1px; border-bottom: 1.5px solid var(--ink-strong); border-left: 1.5px solid var(--ink-strong); }}
    .tick-br {{ bottom: -1px; right: -1px; border-bottom: 1.5px solid var(--ink-strong); border-right: 1.5px solid var(--ink-strong); }}
    /* Sticky Top HUD Header */
    .top-nav {{
      position: sticky;
      top: 0;
      z-index: 50;
      height: 48px;
      background: var(--bg-glass);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--line);
    }}
    .top-nav-inner {{
      max-width: 1280px;
      height: 100%;
      margin: 0 auto;
      padding: 0 20px;
      border-left: 1px solid var(--line);
      border-right: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-family: var(--font-display);
      font-weight: 700;
      font-size: 15px;
      letter-spacing: -0.02em;
      color: var(--ink-strong);
    }}
    .brand svg {{
      width: 22px;
      height: 18px;
      fill: currentColor;
      flex-shrink: 0;
    }}
    .brand-badge {{
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      padding: 2px 7px;
      border: 1px solid var(--line-strong);
      color: var(--accent-ink);
      background: rgba(45, 129, 255, 0.08);
    }}
    .nav-links {{
      display: flex;
      align-items: center;
      gap: 22px;
    }}
    .nav-links a {{
      font-family: var(--font-mono);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: var(--muted);
      transition: color 0.15s ease;
    }}
    .nav-links a:hover {{
      color: var(--ink-strong);
    }}
    .nav-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .icon-btn {{
      height: 30px;
      padding: 0 10px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      border: 1px solid var(--line);
      background: transparent;
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .icon-btn:hover {{
      color: var(--ink-strong);
      border-color: var(--line-strong);
      background: var(--bg-raised);
    }}
    .nav-cta {{
      height: 30px;
      padding: 0 12px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--invert-bg);
      color: var(--invert-fg);
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      transition: opacity 0.15s ease;
    }}
    .nav-cta:hover {{
      opacity: 0.86;
    }}
    /* Main Architectural Frame */
    .frame {{
      max-width: 1280px;
      margin: 0 auto;
      border-left: 1px solid var(--line);
      border-right: 1px solid var(--line);
    }}
    /* Sticky Numbered Section Eyebrow Bar */
    .section-bar {{
      position: sticky;
      top: 48px;
      z-index: 30;
      min-height: 40px;
      padding: 8px 24px;
      background: var(--bg-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .section-bar-left {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .section-dot {{
      width: 6px;
      height: 6px;
      background: var(--accent);
      display: inline-block;
    }}
    /* Hero Section */
    .hero-grid {{
      display: grid;
      grid-template-columns: 7fr 5fr;
      border-bottom: 1px solid var(--line);
    }}
    .hero-left {{
      position: relative;
      padding: 56px 48px;
      border-right: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 32px;
      background:
        radial-gradient(circle at 12% 15%, rgba(45, 129, 255, 0.09), transparent 52%),
        var(--bg);
    }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      align-self: flex-start;
      padding: 5px 11px;
      border: 1px solid var(--line);
      background: var(--bg-raised);
    }}
    .pulse-dot {{
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: var(--emerald);
      box-shadow: 0 0 10px var(--emerald);
    }}
    .hero-title {{
      font-size: clamp(2.5rem, 5.2vw, 4.5rem);
      color: var(--ink-strong);
      margin: 18px 0 20px;
    }}
    .hero-title .font-serif {{
      font-weight: 400;
      color: var(--accent-ink);
      padding-right: 4px;
    }}
    .hero-lead {{
      font-size: clamp(1rem, 1.35vw, 1.14rem);
      line-height: 1.65;
      color: var(--muted);
      max-width: 620px;
    }}
    .hero-lead strong {{
      color: var(--ink-strong);
      font-weight: 600;
    }}
    .hero-cta-row {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }}
    .btn-mono-primary {{
      height: 44px;
      padding: 0 20px;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      background: var(--invert-bg);
      color: var(--invert-fg);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      transition: transform 0.15s ease, opacity 0.15s ease;
    }}
    .btn-mono-primary:hover {{
      opacity: 0.9;
      transform: translateY(-1px);
    }}
    .btn-mono-outline {{
      height: 44px;
      padding: 0 16px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--line-strong);
      background: var(--bg-raised);
      color: var(--ink-strong);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.13em;
      text-transform: uppercase;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .btn-mono-outline:hover {{
      background: var(--invert-bg);
      color: var(--invert-fg);
      border-color: var(--invert-bg);
    }}
    /* Right Hero Column: Interactive 13-App Dock */
    .hero-right {{
      padding: 36px 32px;
      background: var(--bg-sunken);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 20px;
    }}
    .dock-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--line);
    }}
    .dock-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }}
    .dock-item {{
      padding: 10px 6px;
      border: 1px solid var(--line);
      background: var(--bg-raised);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 7px;
      text-align: center;
      transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
    }}
    .dock-item:hover {{
      transform: translateY(-3px);
      border-color: var(--app);
      box-shadow: 0 8px 20px -6px rgba(0, 0, 0, 0.35);
    }}
    .dock-icon-wrap {{
      width: 44px;
      height: 44px;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid var(--line);
      box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    .dock-icon-wrap img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .dock-label {{
      font-family: var(--font-mono);
      font-size: 9.5px;
      font-weight: 600;
      letter-spacing: 0.04em;
      color: var(--ink-strong);
      white-space: nowrap;
    }}
    .dock-craft {{
      font-style: normal;
      color: var(--app-light);
    }}
    :root[data-theme="dark"] .dock-craft {{
      color: var(--app-dark);
    }}
    .dock-footer {{
      padding-top: 12px;
      border-top: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-family: var(--font-mono);
      font-size: 10.5px;
      color: var(--muted);
    }}
    /* 4-Column Architectural Stat Bar */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      background: var(--line);
      gap: 1px;
      border-bottom: 1px solid var(--line);
    }}
    .stat-cell {{
      background: var(--bg);
      padding: 22px 26px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .stat-num {{
      font-family: var(--font-display);
      font-size: 28px;
      font-weight: 700;
      color: var(--ink-strong);
      letter-spacing: -0.03em;
    }}
    .stat-title {{
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--accent-ink);
    }}
    .stat-sub {{
      font-size: 12.5px;
      color: var(--muted);
    }}
    /* Infinite Marquee Strip */
    .marquee-wrap {{
      overflow: hidden;
      background: var(--bg-sunken);
      border-bottom: 1px solid var(--line);
      padding: 11px 0;
      user-select: none;
    }}
    .marquee-track {{
      display: flex;
      width: max-content;
      animation: artcraft-marquee 42s linear infinite;
    }}
    .marquee-wrap:hover .marquee-track {{
      animation-play-state: paused;
    }}
    .marquee-item {{
      display: inline-flex;
      align-items: center;
      gap: 12px;
      padding: 0 22px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--muted);
      white-space: nowrap;
    }}
    .marquee-item b {{
      color: var(--ink-strong);
      font-weight: 600;
    }}
    .marquee-sq {{
      width: 5px;
      height: 5px;
      background: var(--accent);
      display: inline-block;
    }}
    @keyframes artcraft-marquee {{
      0% {{ transform: translateX(0); }}
      100% {{ transform: translateX(-50%); }}
    }}
    /* Filter Controls inside Section 02 Bar */
    .filter-controls {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .filter-btn {{
      height: 28px;
      padding: 0 11px;
      border: 1px solid var(--line);
      background: transparent;
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.13em;
      text-transform: uppercase;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .filter-btn:hover {{
      color: var(--ink-strong);
      border-color: var(--line-strong);
    }}
    .filter-btn.active {{
      background: var(--invert-bg);
      color: var(--invert-fg);
      border-color: var(--invert-bg);
    }}
    .search-input {{
      height: 28px;
      padding: 0 10px;
      border: 1px solid var(--line);
      background: var(--bg-raised);
      color: var(--ink-strong);
      font-family: var(--font-mono);
      font-size: 11px;
      outline: none;
      width: 180px;
      transition: border-color 0.15s ease;
    }}
    .search-input:focus {{
      border-color: var(--accent);
    }}
    /* 13-App Lineup Grid (1px Hairline Architecture) */
    .lineup-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      background: var(--line);
      gap: 1px;
      border-bottom: 1px solid var(--line);
    }}
    .app-card {{
      position: relative;
      background: var(--bg);
      display: flex;
      flex-direction: column;
      transition: background-color 0.2s ease;
    }}
    .app-card:hover {{
      background: var(--bg-raised);
    }}
    .card-accent-bar {{
      height: 2px;
      width: 100%;
      background: var(--app);
      transform: scaleX(0.28);
      transform-origin: left;
      transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
    }}
    .app-card:hover .card-accent-bar {{
      transform: scaleX(1);
    }}
    .card-hud {{
      padding: 12px 24px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }}
    .card-hud-left {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .num-badge {{
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.12em;
      padding: 2px 6px;
      background: var(--app);
      color: #000000;
    }}
    .card-role {{
      color: var(--ink-strong);
      font-weight: 600;
    }}
    .card-equiv {{
      color: var(--muted);
    }}
    /* 16:10 Official App Workspace Preview */
    .card-preview {{
      position: relative;
      aspect-ratio: 16 / 9.4;
      width: 100%;
      overflow: hidden;
      background:
        radial-gradient(circle at 80% 20%, color-mix(in srgb, var(--app) 28%, transparent), transparent 60%),
        var(--bg-sunken);
      border-bottom: 1px solid var(--line);
      display: block;
    }}
    .card-preview img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: top center;
      display: block;
      transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1);
    }}
    .app-card:hover .card-preview img {{
      transform: scale(1.03);
    }}
    .preview-pill {{
      position: absolute;
      top: 12px;
      right: 12px;
      padding: 3px 8px;
      background: rgba(10, 11, 14, 0.78);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
      border: 1px solid rgba(255, 255, 255, 0.16);
      color: #f2f1ee;
      font-family: var(--font-mono);
      font-size: 9.5px;
      font-weight: 600;
      letter-spacing: 0.14em;
    }}
    /* Card Content Body */
    .card-body {{
      padding: 22px 26px 26px;
      display: flex;
      flex-direction: column;
      flex: 1;
      gap: 16px;
    }}
    .card-title-row {{
      display: flex;
      align-items: flex-end;
      gap: 14px;
      margin-top: -42px;
      position: relative;
      z-index: 2;
    }}
    .card-icon-float {{
      width: 68px;
      height: 68px;
      border-radius: 16px;
      overflow: hidden;
      border: 2px solid var(--bg);
      background: var(--bg-raised);
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.38);
      flex-shrink: 0;
    }}
    .card-icon-float img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .card-title-group {{
      flex: 1;
      padding-bottom: 2px;
    }}
    .card-title {{
      font-family: var(--font-display);
      font-size: 26px;
      font-weight: 700;
      letter-spacing: -0.03em;
      line-height: 1.05;
      color: var(--ink-strong);
    }}
    .craft-accent {{
      color: var(--app-light);
    }}
    :root[data-theme="dark"] .craft-accent {{
      color: var(--app-dark);
    }}
    .card-cat-sub {{
      font-family: var(--font-mono);
      font-size: 10px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--faint);
      margin-top: 3px;
    }}
    .card-quick-arrow {{
      width: 34px;
      height: 34px;
      border: 1px solid var(--line);
      background: var(--bg-raised);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-mono);
      font-size: 14px;
      color: var(--muted);
      transition: all 0.15s ease;
    }}
    .app-card:hover .card-quick-arrow {{
      border-color: var(--app);
      background: var(--app);
      color: #000000;
    }}
    .card-desc {{
      font-size: 14.5px;
      line-height: 1.6;
      color: var(--muted);
      flex: 1;
    }}
    .card-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .tag {{
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 500;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 4px 8px;
      border: 1px solid var(--line);
      background: var(--bg-sunken);
      color: var(--muted);
    }}
    .card-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding-top: 6px;
    }}
    .btn-launch {{
      flex: 1;
      height: 40px;
      padding: 0 16px;
      background: var(--invert-bg);
      color: var(--invert-fg);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      display: inline-flex;
      align-items: center;
      justify-content: space-between;
      transition: background-color 0.15s ease, color 0.15s ease;
    }}
    .btn-launch:hover {{
      background: var(--app);
      color: #000000;
    }}
    .btn-sub {{
      height: 40px;
      padding: 0 12px;
      border: 1px solid var(--line-strong);
      background: transparent;
      color: var(--ink-strong);
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
    }}
    .btn-sub:hover {{
      border-color: var(--app);
      color: var(--app-light);
      background: var(--bg-sunken);
    }}
    :root[data-theme="dark"] .btn-sub:hover {{
      color: var(--app-dark);
    }}
    /* Section 03: iPadOS Touch & Desktop Engine Grid */
    .engine-intro {{
      padding: 44px 48px 36px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 24px;
    }}
    .engine-intro h2 {{
      font-size: clamp(1.85rem, 3.3vw, 2.75rem);
      color: var(--ink-strong);
      max-width: 680px;
    }}
    .engine-intro p {{
      font-size: 14.5px;
      line-height: 1.6;
      color: var(--muted);
      max-width: 440px;
    }}
    .engine-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      background: var(--line);
      gap: 1px;
      border-bottom: 1px solid var(--line);
    }}
    .engine-card {{
      background: var(--bg);
      padding: 28px 26px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .engine-num {{
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 600;
      letter-spacing: 0.14em;
      color: var(--accent-ink);
      text-transform: uppercase;
    }}
    .engine-card h3 {{
      font-family: var(--font-display);
      font-size: 19px;
      font-weight: 700;
      color: var(--ink-strong);
      letter-spacing: -0.02em;
    }}
    .engine-card p {{
      font-size: 13.5px;
      line-height: 1.6;
      color: var(--muted);
      flex: 1;
    }}
    .engine-Spec {{
      padding-top: 12px;
      border-top: 1px solid var(--line);
      font-family: var(--font-mono);
      font-size: 10px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--faint);
    }}
    /* Section 04: Installation & Auto-Update Blueprint */
    .install-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      background: var(--line);
      gap: 1px;
      border-bottom: 1px solid var(--line);
    }}
    .install-col {{
      background: var(--bg);
      padding: 38px 40px;
      display: flex;
      flex-direction: column;
      gap: 22px;
    }}
    .install-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--line);
    }}
    .install-title {{
      font-family: var(--font-display);
      font-size: 22px;
      font-weight: 700;
      color: var(--ink-strong);
    }}
    .step-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .step-item {{
      display: grid;
      grid-template-columns: 32px 1fr;
      gap: 12px;
      align-items: start;
    }}
    .step-idx {{
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      padding: 4px 0;
      text-align: center;
      border: 1px solid var(--line-strong);
      background: var(--bg-sunken);
      color: var(--ink-strong);
    }}
    .step-text {{
      font-size: 14px;
      line-height: 1.55;
      color: var(--muted);
    }}
    .step-text strong {{
      color: var(--ink-strong);
      font-weight: 600;
    }}
    /* Architectural Footer */
    .footer {{
      padding: 48px 40px 56px;
      background: var(--bg-sunken);
      display: flex;
      flex-direction: column;
      gap: 36px;
    }}
    .footer-top {{
      display: grid;
      grid-template-columns: 1.2fr 2fr;
      gap: 40px;
      padding-bottom: 32px;
      border-bottom: 1px solid var(--line);
    }}
    .footer-brand-col {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .footer-brand-col p {{
      font-size: 13.5px;
      line-height: 1.6;
      color: var(--muted);
      max-width: 360px;
    }}
    .footer-apps-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px 16px;
    }}
    .footer-link {{
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--ink-strong);
      padding: 4px 0;
      transition: color 0.15s ease;
    }}
    .footer-link span {{
      color: var(--faint);
      font-size: 10px;
    }}
    .footer-link:hover {{
      color: var(--accent-ink);
    }}
    .footer-bottom {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--muted);
    }}
    .footer-bottom a {{
      color: var(--ink-strong);
      text-decoration: underline;
      text-underline-offset: 3px;
    }}
    /* Responsive Breakpoints */
    @media (max-width: 1080px) {{
      .hero-grid {{
        grid-template-columns: 1fr;
      }}
      .hero-left {{
        border-right: none;
        border-bottom: 1px solid var(--line);
        padding: 40px 28px;
      }}
      .stats-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .engine-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .install-grid {{
        grid-template-columns: 1fr;
      }}
      .footer-top {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 780px) {{
      .nav-links {{
        display: none;
      }}
      .lineup-grid {{
        grid-template-columns: 1fr;
      }}
      .engine-grid {{
        grid-template-columns: 1fr;
      }}
      .stats-grid {{
        grid-template-columns: 1fr;
      }}
      .footer-apps-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .engine-intro, .install-col, .footer {{
        padding: 28px 20px;
      }}
    }}
  </style>
</head>
<body>
  <!-- Sticky Top HUD Bar -->
  <header class="top-nav">
    <div class="top-nav-inner">
      <a href="#" class="brand">
        <svg viewBox="0 0 116.34 97.5" aria-hidden="true">
          <path d="M104.28,49.49L81.55,0h-31.23l-3.17,4.76L14.75,53.63,0,75.85l21.55,21.55,63.79-36.94,16.99,37.04,14.01-21.74-12.06-26.27ZM32.89,65.66l32.42-48.87,10.91,23.77-43.32,25.09Z"/>
        </svg>
        <span>ArtCraft</span>
        <span class="brand-badge">iPadOS Suite</span>
      </a>
      <nav class="nav-links" aria-label="Primary Navigation">
        <a href="#lineup">01 / Lineup (13)</a>
        <a href="#engine">02 / iPadOS Engine</a>
        <a href="#install">03 / Install Guide</a>
        <a href="https://github.com/Milanista86/craft-ipad-apps/releases/tag/v1.0.0" target="_blank" rel="noopener noreferrer">04 / Releases (.ipa)</a>
      </nav>
      <div class="nav-actions">
        <button type="button" id="themeToggle" class="icon-btn" title="Switch Light / Dark Appearance">
          <span id="themeIcon">☀</span>
          <span id="themeLabel">Theme</span>
        </button>
        <a href="https://github.com/Milanista86/craft-ipad-apps" target="_blank" rel="noopener noreferrer" class="icon-btn" title="GitHub Repository">
          GitHub ↗
        </a>
        <a href="#lineup" class="nav-cta">Launch Apps ↓</a>
      </div>
    </div>
  </header>
  <main class="frame">
    <!-- Section 01: Hero & Interactive 13-App Dock -->
    <div class="section-bar">
      <div class="section-bar-left">
        <span class="section-dot"></span>
        <span class="hud-label">01 / ArtCraft Suite for iPadOS</span>
      </div>
      <span class="hud-label">Thirteen Apps &middot; Pure Rust + WebAssembly &middot; Open Source</span>
    </div>
    <section class="hero-grid">
      <div class="hero-left">
        <span class="tick tick-tl"></span>
        <span class="tick tick-tr"></span>
        <span class="tick tick-bl"></span>
        <span class="tick tick-br"></span>
        <div>
          <div class="status-pill">
            <span class="pulse-dot"></span>
            <span class="hud-label" style="color: var(--ink-strong);">Live Cloud Hub &middot; Auto-Synced Weekly from @storytold</span>
          </div>
          <h1 class="font-display hero-title">
            Thirteen apps.<br>
            One <span class="font-serif">craft</span> — on iPadOS.
          </h1>
          <p class="hero-lead">
            The complete open-source creative, office, audio, and CAD desktop suite by <strong><a href="https://getartcraft.com" target="_blank" rel="noopener noreferrer" style="text-decoration: underline; text-underline-offset: 3px;">ArtCraft (@storytold)</a></strong>, engineered to run fullscreen on your iPad. Enjoy <strong>100% desktop mouse, trackpad &amp; keyboard fidelity</strong> alongside a draggable Apple Pencil tool dock, Procreate-style multi-touch gestures, and native iPadOS Files integration.
          </p>
        </div>
        <div class="hero-cta-row">
          <a href="#lineup" class="btn-mono-primary">
            <span>Explore All 13 Apps</span>
            <span>↓</span>
          </a>
          <a href="https://github.com/Milanista86/craft-ipad-apps/releases/tag/v1.0.0" target="_blank" rel="noopener noreferrer" class="btn-mono-outline">
            <span>↓ Download .IPA Suite</span>
          </a>
          <button type="button" id="copyHubBtn" class="btn-mono-outline">
            <span id="copyHubText">Copy Hub Link</span>
          </button>
        </div>
      </div>
      <div class="hero-right">
        <div class="dock-header">
          <span class="hud-label" style="color: var(--ink-strong);">Interactive App Dock (13)</span>
          <span class="hud-label">Tap Icon to Jump ↓</span>
        </div>
        <div class="dock-grid">
{dock_html}
        </div>
        <div class="dock-footer">
          <span>7 CREATIVE &amp; DESIGN</span>
          <span>&bull;</span>
          <span>6 OFFICE, AUDIO &amp; CAD</span>
        </div>
      </div>
    </section>
    <!-- 4-Column Architectural Stat Bar -->
    <section class="stats-grid" aria-label="Suite Highlights">
      <div class="stat-cell">
        <div class="stat-num">13 Apps</div>
        <div class="stat-title">Complete Desktop Suite</div>
        <div class="stat-sub">Photo, Vector, Layout, RAW, Video, VFX, UI, Office, PDF, DAW &amp; CAD</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num">100%</div>
        <div class="stat-title">Desktop Mouse &amp; Keyboard</div>
        <div class="stat-sub">Passive touch layer leaves Magic Keyboard, trackpad &amp; mice untouched</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num">2 Modes</div>
        <div class="stat-title">Cloud PWA + Native .IPA</div>
        <div class="stat-sub">Install directly from Safari or sideload edge-to-edge native .ipa</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num">$0 / Forever</div>
        <div class="stat-title">Open Source &amp; Auto-Updated</div>
        <div class="stat-sub">No subscriptions, no accounts, no telemetry &middot; MIT / Apache-2.0</div>
      </div>
    </section>
    <!-- Infinite Scrolling Marquee Ticker -->
    <div class="marquee-wrap" aria-hidden="true">
      <div class="marquee-track">
        <span class="marquee-item"><span class="marquee-sq"></span> <b>NATIVE IPADOS FILES SHARE SHEET</b></span>
        <span class="marquee-item"><span class="marquee-sq"></span> PROCREATE-STYLE <b>2-FINGER UNDO &amp; 3-FINGER REDO</b></span>
        <span class="marquee-item"><span class="marquee-sq"></span> DRAGGABLE FLOATING <b>TOUCH &amp; APPLE PENCIL DOCK (⚙️)</b></span>
        <span class="marquee-item"><span class="marquee-sq"></span> <b>100% DESKTOP</b> MOUSE, TRACKPAD &amp; KEYBOARD FIDELITY</span>
        <span class="marquee-item"><span class="marquee-sq"></span> PURE <b>RUST + WEBASSEMBLY</b> ENGINE</span>
        <span class="marquee-item"><span class="marquee-sq"></span> <b>AUTO-UPDATED WEEKLY</b> VIA GITHUB ACTIONS</span>
        <span class="marquee-item"><span class="marquee-sq"></span> <b>NATIVE IPADOS FILES SHARE SHEET</b></span>
        <span class="marquee-item"><span class="marquee-sq"></span> PROCREATE-STYLE <b>2-FINGER UNDO &amp; 3-FINGER REDO</b></span>
        <span class="marquee-item"><span class="marquee-sq"></span> DRAGGABLE FLOATING <b>TOUCH &amp; APPLE PENCIL DOCK (⚙️)</b></span>
        <span class="marquee-item"><span class="marquee-sq"></span> <b>100% DESKTOP</b> MOUSE, TRACKPAD &amp; KEYBOARD FIDELITY</span>
        <span class="marquee-item"><span class="marquee-sq"></span> PURE <b>RUST + WEBASSEMBLY</b> ENGINE</span>
        <span class="marquee-item"><span class="marquee-sq"></span> <b>AUTO-UPDATED WEEKLY</b> VIA GITHUB ACTIONS</span>
      </div>
    </div>
    <!-- Section 02: The Lineup -->
    <div id="lineup" class="section-bar">
      <div class="section-bar-left">
        <span class="section-dot"></span>
        <span class="hud-label">02 / The Lineup — All Thirteen Applications</span>
      </div>
      <div class="filter-controls">
        <button type="button" class="filter-btn active" data-filter="all">All (13)</button>
        <button type="button" class="filter-btn" data-filter="creative">Creative &amp; Design (7)</button>
        <button type="button" class="filter-btn" data-filter="office">Office, Audio &amp; CAD (6)</button>
        <input type="search" id="appSearch" class="search-input" placeholder="Search apps or formats...">
      </div>
    </div>
    <section class="lineup-grid" aria-label="Applications Lineup">
{lineup_html}
    </section>
    <!-- Section 03: iPadOS Touch & Desktop Engine -->
    <div id="engine" class="section-bar">
      <div class="section-bar-left">
        <span class="section-dot"></span>
        <span class="hud-label">03 / iPadOS Touch &amp; Desktop Architecture</span>
      </div>
      <span class="hud-label">Zero Interference with Mouse, Trackpad &amp; Physical Keyboard</span>
    </div>
    <div class="engine-intro">
      <h2 class="font-display">
        Built for <span class="font-serif">touch</span> when you hold it.<br>
        Pure <span class="font-serif">desktop</span> when you dock it.
      </h2>
      <p>
        Every iPadOS upgrade runs inside a passive overlay layer. When you attach a Magic Keyboard, external mouse, or trackpad, all native cursor events, hover states, right-clicks, and keyboard shortcuts work identically to macOS and Windows.
      </p>
    </div>
    <section class="engine-grid">
      <div class="engine-card">
        <span class="engine-num">01 / Floating Dock (⚙️)</span>
        <h3>Draggable Tool Pill</h3>
        <p>
          Press and drag the subtle <strong>⚙️</strong> button anywhere along the screen edges—each app remembers your preferred spot. Tap to open quick buttons for <strong>↩️ Undo</strong>, <strong>↪️ Redo</strong>, <strong>⌫ Delete</strong>, <strong>Right-Click</strong>, <strong>⌨️ Keyboard</strong>, and <strong>🔄 Instant Cloud Reload</strong>.
        </p>
        <div class="engine-Spec">Position Saved in LocalStorage</div>
      </div>
      <div class="engine-card">
        <span class="engine-num">02 / Procreate Gestures</span>
        <h3>Multi-Touch Shortcuts</h3>
        <p>
          Work without a physical keyboard effortlessly: <strong>Two-finger quick tap</strong> triggers Undo (<code>Ctrl+Z</code>), <strong>Three-finger quick tap</strong> triggers Redo (<code>Ctrl+Y</code>), and <strong>Two-finger pinch</strong> smoothly zooms the canvas in or out.
        </p>
        <div class="engine-Spec">100% Passive Touch Listeners</div>
      </div>
      <div class="engine-card">
        <span class="engine-num">03 / Native Files Bridge</span>
        <h3>Save to iPadOS Files</h3>
        <p>
          Exporting a PSD, SVG, DOCX, XLSX, PDF, WAV, or DXF automatically invokes the native <strong>iPadOS Share &amp; Save to Files sheet</strong> so you can save directly to iCloud Drive, On My iPad, or AirDrop, backed by persistent browser storage.
        </p>
        <div class="engine-Spec">Web Share Level 2 + Storage Lock</div>
      </div>
      <div class="engine-card">
        <span class="engine-num">04 / Status Bar Layout</span>
        <h3>Precision Top Menu Offset</h3>
        <p>
          Precision-tuned <code>18px</code> top safe-area offset in Safari Home Screen mode keeps the iPadOS clock and battery bar from overlapping the top menu bar (<code>File Edit Image Layer...</code>), or <code>0px</code> edge-to-edge in the native <code>.ipa</code>.
        </p>
        <div class="engine-Spec">Auto-Detected Standalone Mode</div>
      </div>
    </section>
    <!-- Section 04: Installation & Auto-Update Guide -->
    <div id="install" class="section-bar">
      <div class="section-bar-left">
        <span class="section-dot"></span>
        <span class="hud-label">04 / Installation &amp; Auto-Update Guide</span>
      </div>
      <span class="hud-label">Choose Cloud Web App (No PC) or Native .IPA Sideload</span>
    </div>
    <section class="install-grid">
      <div class="install-col">
        <div class="install-head">
          <div class="install-title">Option A — Cloud Web App (Recommended)</div>
          <span class="brand-badge">No PC Required</span>
        </div>
        <ol class="step-list">
          <li class="step-item">
            <span class="step-idx">01</span>
            <div class="step-text">Open this page in <strong>Safari</strong> on your iPad, iPad Air, iPad mini, or iPad Pro.</div>
          </li>
          <li class="step-item">
            <span class="step-idx">02</span>
            <div class="step-text">Tap <strong>Launch</strong> on any of the 13 applications above and wait a moment for the workspace to appear.</div>
          </li>
          <li class="step-item">
            <span class="step-idx">03</span>
            <div class="step-text">Tap the Safari <strong>Share</strong> button (square with upward arrow) and select <strong>Add to Home Screen</strong>.</div>
          </li>
          <li class="step-item">
            <span class="step-idx">04</span>
            <div class="step-text"><strong>Automatic Updates:</strong> Our GitHub Actions bot checks <a href="https://github.com/storytold" target="_blank" rel="noopener noreferrer" style="text-decoration: underline;">@storytold</a> every Sunday at 03:00 UTC. Tap <strong>⚙️ &rarr; 🔄</strong> inside any app to pull the newest build immediately.</div>
          </li>
        </ol>
      </div>
      <div class="install-col">
        <div class="install-head">
          <div class="install-title">Option B — Native .IPA Sideload</div>
          <span class="brand-badge">Zero Status Bar &middot; Offline</span>
        </div>
        <ol class="step-list">
          <li class="step-item">
            <span class="step-idx">01</span>
            <div class="step-text">Tap <strong>&darr; .IPA</strong> on any app card above (or visit <a href="https://github.com/Milanista86/craft-ipad-apps/releases/tag/v1.0.0" target="_blank" rel="noopener noreferrer" style="text-decoration: underline;">GitHub Releases</a>) to download <code>&lt;AppName&gt;-iPad.ipa</code>.</div>
          </li>
          <li class="step-item">
            <span class="step-idx">02</span>
            <div class="step-text">Import and sign the <code>.ipa</code> directly on your iPad using <strong>Feather</strong>, <strong>ESign</strong>, <strong>GBox</strong>, <strong>SideStore</strong>, or <strong>Sideloadly</strong>.</div>
          </li>
          <li class="step-item">
            <span class="step-idx">03</span>
            <div class="step-text">Enjoy <strong>true edge-to-edge fullscreen</strong> with the iPadOS Status Bar &amp; Home Indicator hidden and 100% offline WebAssembly execution.</div>
          </li>
          <li class="step-item">
            <span class="step-idx">04</span>
            <div class="step-text">Whenever upstream releases a new version, run the <strong>Build All 13 Native iPadOS (.ipa) Apps</strong> workflow in GitHub Actions to generate fresh <code>.ipa</code> installers.</div>
          </li>
        </ol>
      </div>
    </section>
    <!-- Footer -->
    <footer class="footer">
      <div class="footer-top">
        <div class="footer-brand-col">
          <div class="brand">
            <svg viewBox="0 0 116.34 97.5" aria-hidden="true">
              <path d="M104.28,49.49L81.55,0h-31.23l-3.17,4.76L14.75,53.63,0,75.85l21.55,21.55,63.79-36.94,16.99,37.04,14.01-21.74-12.06-26.27ZM32.89,65.66l32.42-48.87,10.91,23.77-43.32,25.09Z"/>
            </svg>
            <span>ArtCraft Suite for iPadOS</span>
          </div>
          <p>
            iPadOS Cloud PWA &amp; Native <code>.ipa</code> distribution maintained by <a href="https://github.com/Milanista86/craft-ipad-apps" target="_blank" rel="noopener noreferrer" style="text-decoration: underline;">Milanista86</a>. Powered by the open-source Rust &amp; WebAssembly creative and office engines from <a href="https://getartcraft.com" target="_blank" rel="noopener noreferrer" style="text-decoration: underline;">getartcraft.com (@storytold)</a>.
          </p>
        </div>
        <div class="footer-apps-grid">
{footer_apps_html}
        </div>
      </div>
      <div class="footer-bottom">
        <div>
          Upstream Engines &amp; Icons &copy; <a href="https://github.com/storytold" target="_blank" rel="noopener noreferrer">ArtCraft (@storytold)</a> &middot; MIT / Apache-2.0 License
        </div>
        <div>
          <a href="https://github.com/Milanista86/craft-ipad-apps" target="_blank" rel="noopener noreferrer">GitHub Repo</a> &middot;
          <a href="https://github.com/Milanista86/craft-ipad-apps/releases" target="_blank" rel="noopener noreferrer">Native .IPA Releases</a> &middot;
          <a href="https://getartcraft.com/apps" target="_blank" rel="noopener noreferrer">Official ArtCraft Website</a>
        </div>
      </div>
    </footer>
  </main>
  <script>
    (function() {{
      // 1. Theme Toggle (Dark / Light)
      var root = document.documentElement;
      var toggleBtn = document.getElementById('themeToggle');
      var themeIcon = document.getElementById('themeIcon');
      var themeLabel = document.getElementById('themeLabel');
      function syncThemeUI() {{
        var current = root.getAttribute('data-theme') || 'dark';
        if (current === 'dark') {{
          themeIcon.textContent = '☀';
          themeLabel.textContent = 'Light';
        }} else {{
          themeIcon.textContent = '☾';
          themeLabel.textContent = 'Dark';
        }}
      }}
      syncThemeUI();
      if (toggleBtn) {{
        toggleBtn.addEventListener('click', function() {{
          var current = root.getAttribute('data-theme') || 'dark';
          var next = current === 'dark' ? 'light' : 'dark';
          root.setAttribute('data-theme', next);
          try {{ localStorage.setItem('artcraft_ipad_theme', next); }} catch (e) {{}}
          syncThemeUI();
        }});
      }}
      // 2. Copy Hub Link Button
      var copyBtn = document.getElementById('copyHubBtn');
      var copyText = document.getElementById('copyHubText');
      if (copyBtn && copyText) {{
        copyBtn.addEventListener('click', function() {{
          var url = window.location.href.split('#')[0];
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(url).then(function() {{
              copyText.textContent = '✓ Copied Link!';
              setTimeout(function() {{ copyText.textContent = 'Copy Hub Link'; }}, 1800);
            }});
          }}
        }});
      }}
      // 3. Category Filter & Live Search
      var filterBtns = document.querySelectorAll('.filter-btn');
      var searchInput = document.getElementById('appSearch');
      var cards = document.querySelectorAll('.app-card');
      var activeCat = 'all';
      function applyFilter() {{
        var q = (searchInput ? searchInput.value : '').trim().toLowerCase();
        cards.forEach(function(card) {{
          var catMatch = (activeCat === 'all') || (card.getAttribute('data-cat') === activeCat);
          var searchBlob = card.getAttribute('data-search') || '';
          var searchMatch = !q || searchBlob.indexOf(q) !== -1;
          card.style.display = (catMatch && searchMatch) ? '' : 'none';
        }});
      }}
      filterBtns.forEach(function(btn) {{
        btn.addEventListener('click', function() {{
          filterBtns.forEach(function(b) {{ b.classList.remove('active'); }});
          btn.classList.add('active');
          activeCat = btn.getAttribute('data-filter') || 'all';
          applyFilter();
        }});
      }});
      if (searchInput) {{
        searchInput.addEventListener('input', applyFilter);
      }}
    }})();
  </script>
</body>
</html>
"""
    (out_root / "index.html").write_text(hub_html, encoding="utf-8")
def main():
    out_root = Path("gh-pages-out")
    shutil.rmtree(out_root, ignore_errors=True)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / ".nojekyll").write_text("", encoding="utf-8")
    (out_root / ".gitattributes").write_text("* -text\n", encoding="utf-8")
    for app_meta in APPS:
        process_app(app_meta, out_root)
    generate_hub_index(out_root)
    print("Successfully built complete 13-app ArtCraft Suite for iPadOS in gh-pages-out/")
if __name__ == "__main__":
    main()
