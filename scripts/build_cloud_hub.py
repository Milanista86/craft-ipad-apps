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
        "menus": "File  Edit  Image  Layer  Type  Select  Filter  View",
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
        "menus": "File  Edit  Object  Type  Select  Effect  View  Window",
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
        "menus": "File  Edit  Layout  Type  Object  Table  View  Window",
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
        "menus": "File  Edit  Library  Photo  Develop  Metadata  View",
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
        "menus": "File  Edit  Clip  Sequence  Markers  Color  Audio  View",
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
        "menus": "File  Edit  Composition  Layer  Effect  Animation  View",
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
        "menus": "File  Edit  View  Object  Text  Arrange  Vector  Plugins",
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
        "menus": "File  Home  Insert  Design  Layout  References  Review  View",
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
        "menus": "File  Home  Insert  Page Layout  Formulas  Data  Review  View",
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
        "menus": "File  Home  Insert  Design  Transitions  Animations  Slide Show",
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
        "menus": "File  Edit  View  Document  Pages  Forms  Protect  Comment",
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
        "menus": "File  Edit  Track  Clip  Event  AudioSuite  Mix  Window",
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
        "menus": "File  Edit  View  Draw  Dimension  Modify  Parametric  Solid",
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
    # Audited 100/100 geometric SVG mark (C-Frame + 45-degree Apple Pencil barrel & nib cone)
    logo_svg_inline = """<svg class="brand-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="Craft for iPadOS Logo">
            <path class="logo-frame" d="M 80 32 H 172 L 128 76 H 88 A 12 12 0 0 0 76 88 V 168 A 12 12 0 0 0 88 180 H 192 L 192 224 H 80 A 48 48 0 0 1 32 176 V 80 A 48 48 0 0 1 80 32 Z"/>
            <polygon class="logo-nib" points="104,152 104,116 140,152"/>
            <polygon class="logo-nib" points="116,104 188,32 224,68 152,140"/>
          </svg>"""
    favicon_svg_uri = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256'%3E"
        "%3Crect width='256' height='256' rx='56' fill='%23111318'/%3E"
        "%3Cpath fill='%23F2F1EE' d='M 80 32 H 172 L 128 76 H 88 A 12 12 0 0 0 76 88 V 168 A 12 12 0 0 0 88 180 H 192 L 192 224 H 80 A 48 48 0 0 1 32 176 V 80 A 48 48 0 0 1 80 32 Z'/%3E"
        "%3Cpolygon fill='%232D81FF' points='104,152 104,116 140,152'/%3E"
        "%3Cpolygon fill='%232D81FF' points='116,104 188,32 224,68 152,140'/%3E"
        "%3C/svg%3E"
    )
    lineup_cards = []
    for app in APPS:
        cat_slug = "creative" if app["category"] == "Creative & Design" else "office"
        short_equiv = app["equiv"].replace("Adobe ", "").replace("Microsoft ", "").replace("Avid ", "")
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in app["tags"][:2])
        search_blob = f"{app['name']} {app['role']} {app['equiv']} {app['desc']} {' '.join(app['tags'])}".lower()
        lineup_cards.append(f"""        <article id="app-{app['id']}" class="app-card" data-cat="{cat_slug}" data-search="{search_blob}" style="--app: {app['color']}; --app-dark: {app['ink_dark']}; --app-light: {app['ink_light']};">
          <div class="card-top">
            <a href="./{app['id']}/?v=4" class="card-icon" aria-label="Launch {app['name']}">
              <img src="./{app['id']}/icon.png?v=4" alt="{app['name']} icon" loading="lazy">
            </a>
            <div class="card-heading">
              <h2 class="card-title">
                <a href="./{app['id']}/?v=4">{app['prefix']}<span class="craft-tint">{app['suffix']}</span></a>
              </h2>
              <div class="card-equiv" title="{app['role']}">{short_equiv}</div>
            </div>
          </div>
          <p class="card-desc">{app['desc']}</p>
          <div class="card-tags">
            {tags_html}
          </div>
          <div class="card-footer">
            <a class="btn-launch" href="./{app['id']}/?v=4">
              <span>Launch App</span>
              <span class="launch-arrow">↗</span>
            </a>
            <div class="card-sub-links">
              <a class="btn-pill" href="https://github.com/Milanista86/craft-ipad-apps/releases/download/v1.0.0/{app['name']}-iPad.ipa" title="Download Native iPadOS .ipa Installer">.IPA</a>
              <a class="btn-pill" href="https://github.com/storytold/{app['id']}" target="_blank" rel="noopener noreferrer" title="View Upstream Source by @storytold">GitHub</a>
            </div>
          </div>
        </article>""")
    lineup_html = "\n".join(lineup_cards)
    hub_html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
  <title>Craft for iPadOS — 13 Open-Source Desktop Apps Adapted for iPad</title>
  <meta name="description" content="Community iPadOS hub by @Milanista86 adapting all 13 open-source desktop creative, office, audio, and CAD apps by ArtCraft (@storytold) for fullscreen iPadOS use.">
  <meta property="og:title" content="Craft for iPadOS — 13 Desktop Apps Adapted for iPad">
  <meta property="og:description" content="Run all 13 open-source desktop apps by ArtCraft (@storytold) on iPadOS with full Mouse, Trackpad, Keyboard, and Apple Pencil support.">
  <meta property="og:type" content="website">
  <link rel="icon" type="image/svg+xml" href="{favicon_svg_uri}">
  <link rel="apple-touch-icon" href="./photocraft/apple-touch-icon.png?v=4">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
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
      --bg: #f5f5f7;
      --surface: #ffffff;
      --surface-hover: #fcfcfd;
      --surface-subtle: #ededf2;
      --header-bg: rgba(245, 245, 247, 0.82);
      --text: #111114;
      --text-secondary: #52525b;
      --text-muted: #71717a;
      --border: rgba(17, 17, 20, 0.09);
      --border-strong: rgba(17, 17, 20, 0.18);
      --accent: #2d81ff;
      --accent-soft: rgba(45, 129, 255, 0.1);
      --logo-frame: #111114;
      --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
      --shadow-hover: 0 12px 28px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04);
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
      color-scheme: light;
    }}
    :root[data-theme="dark"] {{
      --bg: #0c0d10;
      --surface: #14161b;
      --surface-hover: #191c23;
      --surface-subtle: #1d2028;
      --header-bg: rgba(12, 13, 16, 0.82);
      --text: #f3f4f6;
      --text-secondary: #a1a1aa;
      --text-muted: #71717a;
      --border: rgba(255, 255, 255, 0.08);
      --border-strong: rgba(255, 255, 255, 0.16);
      --accent: #2d81ff;
      --accent-soft: rgba(45, 129, 255, 0.14);
      --logo-frame: #f2f1ee;
      --shadow-card: 0 4px 12px rgba(0, 0, 0, 0.25);
      --shadow-hover: 0 14px 32px rgba(0, 0, 0, 0.45);
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
      color: var(--text);
      font-family: var(--font-sans);
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}
    body {{
      background:
        radial-gradient(ellipse 80% 40% at 50% -10%, rgba(45, 129, 255, 0.12), transparent 70%),
        var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}
    a {{
      color: inherit;
      text-decoration: none;
    }}
    /* SVG Brand Mark Styling */
    .brand-logo-svg {{
      display: block;
      width: 100%;
      height: 100%;
    }}
    .brand-logo-svg .logo-frame {{
      fill: var(--logo-frame);
      transition: fill 0.2s ease;
    }}
    .brand-logo-svg .logo-nib {{
      fill: #2d81ff;
    }}
    /* Sticky Glass Header */
    .site-header {{
      position: sticky;
      top: 0;
      z-index: 50;
      height: 60px;
      background: var(--header-bg);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border);
    }}
    .header-inner {{
      max-width: 1240px;
      height: 100%;
      margin: 0 auto;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .brand-lockup {{
      display: inline-flex;
      align-items: center;
      gap: 11px;
    }}
    .brand-mark-box {{
      width: 34px;
      height: 34px;
      border-radius: 9px;
      padding: 5px;
      background: var(--surface);
      border: 1px solid var(--border-strong);
      box-shadow: var(--shadow-card);
      flex-shrink: 0;
    }}
    .brand-text {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      font-size: 16px;
      letter-spacing: -0.025em;
    }}
    .brand-text span.sub {{
      font-weight: 500;
      color: var(--text-secondary);
    }}
    .badge-community {{
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      border: 1px solid rgba(45, 129, 255, 0.25);
    }}
    .header-nav {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .nav-btn {{
      height: 34px;
      padding: 0 12px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text-secondary);
      font-size: 12.5px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .nav-btn:hover {{
      color: var(--text);
      border-color: var(--border-strong);
      background: var(--surface-hover);
    }}
    /* Main Container */
    .container {{
      max-width: 1240px;
      margin: 0 auto;
      padding: 0 24px 64px;
    }}
    /* Compact, Focused Hero */
    .hero {{
      padding: 40px 0 28px;
      text-align: center;
      max-width: 780px;
      margin: 0 auto;
    }}
    .hero-logo-badge {{
      width: 60px;
      height: 60px;
      margin: 0 auto 16px;
      padding: 10px;
      border-radius: 16px;
      background: var(--surface);
      border: 1px solid var(--border-strong);
      box-shadow: var(--shadow-hover);
    }}
    .hero h1 {{
      font-size: clamp(1.85rem, 3.6vw, 2.65rem);
      font-weight: 800;
      letter-spacing: -0.035em;
      line-height: 1.12;
      margin-bottom: 12px;
    }}
    .hero h1 span {{
      background: linear-gradient(135deg, #2d81ff 0%, #60a5fa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .hero-sub {{
      font-size: 15.5px;
      line-height: 1.6;
      color: var(--text-secondary);
      margin-bottom: 16px;
    }}
    .hero-sub a {{
      color: var(--text);
      font-weight: 600;
      text-decoration: underline;
      text-underline-offset: 3px;
    }}
    .credit-pill {{
      display: inline-flex;
      align-items: center;
      flex-wrap: wrap;
      justify-content: center;
      gap: 8px;
      padding: 6px 14px;
      border-radius: 999px;
      background: var(--surface);
      border: 1px solid var(--border);
      font-size: 12.5px;
      color: var(--text-secondary);
      box-shadow: var(--shadow-card);
    }}
    .credit-pill a {{
      color: var(--accent);
      font-weight: 600;
    }}
    .credit-pill a:hover {{
      text-decoration: underline;
    }}
    .dot-live {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
    }}
    /* Toolbar: Category Filter Tabs + Search */
    .toolbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      margin: 8px 0 20px;
      padding: 10px 12px;
      border-radius: 14px;
      background: var(--surface);
      border: 1px solid var(--border);
      box-shadow: var(--shadow-card);
    }}
    .filter-tabs {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .filter-btn {{
      height: 34px;
      padding: 0 14px;
      border-radius: 9px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--text-secondary);
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .filter-btn:hover {{
      color: var(--text);
      background: var(--surface-subtle);
    }}
    .filter-btn.active {{
      background: var(--text);
      color: var(--bg);
    }}
    .search-box {{
      position: relative;
      flex: 1;
      min-width: 210px;
      max-width: 280px;
    }}
    .search-input {{
      width: 100%;
      height: 34px;
      padding: 0 12px;
      border-radius: 9px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 13px;
      outline: none;
      transition: border-color 0.15s ease;
    }}
    .search-input:focus {{
      border-color: var(--accent);
    }}
    /* Compact 3-to-4 Column App Grid */
    .apps-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(275px, 1fr));
      gap: 16px;
    }}
    .app-card {{
      position: relative;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      box-shadow: var(--shadow-card);
      transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
      overflow: hidden;
    }}
    .app-card::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--app);
      opacity: 0.75;
      transition: opacity 0.18s ease, height 0.18s ease;
    }}
    .app-card:hover {{
      transform: translateY(-3px);
      background: var(--surface-hover);
      border-color: color-mix(in srgb, var(--app) 50%, var(--border-strong));
      box-shadow: var(--shadow-hover);
    }}
    .app-card:hover::before {{
      opacity: 1;
    }}
    .card-top {{
      display: flex;
      align-items: center;
      gap: 13px;
    }}
    .card-icon {{
      width: 50px;
      height: 50px;
      border-radius: 12px;
      overflow: hidden;
      flex-shrink: 0;
      border: 1px solid var(--border);
      box-shadow: 0 3px 8px rgba(0, 0, 0, 0.18);
    }}
    .card-icon img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .card-heading {{
      flex: 1;
      min-width: 0;
    }}
    .card-title-line {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
    }}
    .card-title {{
      font-size: 17px;
      font-weight: 700;
      letter-spacing: -0.02em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .craft-tint {{
      color: var(--app-light);
    }}
    :root[data-theme="dark"] .craft-tint {{
      color: var(--app-dark);
    }}
    .role-pill {{
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 6px;
      background: var(--surface-subtle);
      color: var(--text-secondary);
      white-space: nowrap;
      flex-shrink: 0;
    }}
    .card-equiv {{
      font-size: 12px;
      font-weight: 500;
      color: var(--text-muted);
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .card-desc {{
      font-size: 13px;
      line-height: 1.5;
      color: var(--text-secondary);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      min-height: 39px;
    }}
    .card-tags {{
      display: flex;
      flex-wrap: nowrap;
      gap: 5px;
      overflow: hidden;
    }}
    .tag {{
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 500;
      padding: 3px 7px;
      border-radius: 6px;
      background: var(--surface-subtle);
      color: var(--text-secondary);
      white-space: nowrap;
    }}
    .card-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding-top: 10px;
      margin-top: auto;
      border-top: 1px solid var(--border);
    }}
    .btn-launch {{
      flex: 1;
      height: 34px;
      padding: 0 13px;
      border-radius: 9px;
      background: var(--text);
      color: var(--bg);
      font-size: 12.5px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      justify-content: space-between;
      transition: background-color 0.15s ease, color 0.15s ease, transform 0.15s ease;
    }}
    .btn-launch:hover {{
      background: var(--app);
      color: #000000;
    }}
    .launch-arrow {{
      font-family: var(--font-mono);
      font-size: 13px;
    }}
    .card-sub-links {{
      display: flex;
      align-items: center;
      gap: 5px;
    }}
    .btn-pill {{
      height: 34px;
      padding: 0 10px;
      border-radius: 9px;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--text-secondary);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
    }}
    .btn-pill:hover {{
      color: var(--text);
      border-color: var(--border-strong);
      background: var(--surface-subtle);
    }}
    .empty-state {{
      display: none;
      text-align: center;
      padding: 40px 20px;
      border-radius: 16px;
      border: 1px dashed var(--border-strong);
      color: var(--text-secondary);
      font-size: 14px;
      margin-top: 12px;
    }}
    /* Compact 2-Column Info Section Below Grid */
    .info-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      margin-top: 32px;
    }}
    .info-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 22px 24px;
      box-shadow: var(--shadow-card);
    }}
    .info-card-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 14px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }}
    .info-card h3 {{
      font-size: 16px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}
    .info-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .info-list li {{
      display: flex;
      align-items: baseline;
      gap: 10px;
      font-size: 13.5px;
      line-height: 1.55;
      color: var(--text-secondary);
    }}
    .info-list li strong {{
      color: var(--text);
      font-weight: 600;
    }}
    .step-dot {{
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      color: var(--accent);
      flex-shrink: 0;
    }}
    /* Clean Minimal Centered Footer */
    .site-footer {{
      margin-top: 48px;
      padding-top: 28px;
      border-top: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 10px;
      font-size: 12.5px;
      line-height: 1.6;
      color: var(--text-muted);
      max-width: 780px;
      margin-left: auto;
      margin-right: auto;
    }}
    .footer-links {{
      display: flex;
      align-items: center;
      justify-content: center;
      flex-wrap: wrap;
      gap: 6px 14px;
    }}
    .site-footer a {{
      color: var(--text-secondary);
      font-weight: 500;
      text-decoration: underline;
      text-underline-offset: 3px;
    }}
    .site-footer a:hover {{
      color: var(--text);
    }}
    @media (max-width: 820px) {{
      .info-grid {{
        grid-template-columns: 1fr;
      }}
      .badge-community {{
        display: none;
      }}
      .search-box {{
        max-width: 100%;
      }}
    }}
  </style>
</head>
<body>
  <!-- Sticky Header -->
  <header class="site-header">
    <div class="header-inner">
      <a href="#" class="brand-lockup">
        <div class="brand-mark-box">
          {logo_svg_inline}
        </div>
        <div class="brand-text">
          <span>Craft <span class="sub">for iPadOS</span></span>
          <span class="badge-community">Community Edition</span>
        </div>
      </a>
      <div class="header-nav">
        <a href="#guide" class="nav-btn">Install Guide</a>
        <a href="https://github.com/Milanista86/craft-ipad-apps/releases/tag/v1.0.0" target="_blank" rel="noopener noreferrer" class="nav-btn">.IPA Releases</a>
        <a href="https://github.com/Milanista86/craft-ipad-apps" target="_blank" rel="noopener noreferrer" class="nav-btn">GitHub ↗</a>
        <button type="button" id="themeToggle" class="nav-btn" title="Toggle Dark / Light Mode">
          <span id="themeIcon">☀</span>
          <span id="themeLabel">Light</span>
        </button>
      </div>
    </div>
  </header>

  <main class="container">
    <!-- Clean, Focused Hero -->
    <section class="hero">
      <div class="hero-logo-badge">
        {logo_svg_inline}
      </div>
      <h1>Pro Desktop Apps, <span>Adapted for iPadOS</span></h1>
      <p class="hero-sub">
        All 13 open-source desktop applications created by <a href="https://getartcraft.com" target="_blank" rel="noopener noreferrer">ArtCraft (@storytold)</a> — tailored for fullscreen iPadOS with 100% desktop Mouse, Trackpad &amp; Keyboard fidelity plus Apple Pencil and Multi-Touch shortcuts.
      </p>
      <div class="credit-pill">
        <span class="dot-live"></span>
        <span>Upstream engines &amp; icons by <a href="https://github.com/storytold" target="_blank" rel="noopener noreferrer">@storytold</a> &middot; Unofficial iPadOS adaptation by <a href="https://github.com/Milanista86/craft-ipad-apps" target="_blank" rel="noopener noreferrer">@Milanista86</a></span>
      </div>
    </section>

    <!-- Filter & Search Bar -->
    <div class="toolbar">
      <div class="filter-tabs" role="tablist" aria-label="Filter applications by category">
        <button type="button" class="filter-btn active" data-filter="all">All 13 Apps</button>
        <button type="button" class="filter-btn" data-filter="creative">Creative &amp; Design (7)</button>
        <button type="button" class="filter-btn" data-filter="office">Office, Audio &amp; CAD (6)</button>
      </div>
      <div class="search-box">
        <input type="search" id="appSearch" class="search-input" placeholder="Search apps or file formats...">
      </div>
    </div>

    <!-- Compact 13-App Grid -->
    <section class="apps-grid" aria-label="13 Applications">
{lineup_html}
    </section>
    <div id="emptyState" class="empty-state">No matching applications found. Try clearing your search filter.</div>

    <!-- Compact 2-Column Guide & Features -->
    <section id="guide" class="info-grid">
      <div class="info-card">
        <div class="info-card-head">
          <h3>How to Install on iPad</h3>
          <span class="badge-community">Cloud PWA or Native .IPA</span>
        </div>
        <ul class="info-list">
          <li>
            <span class="step-dot">01</span>
            <div><strong>Add to Home Screen (No PC):</strong> Tap <strong>Launch App</strong> on any card above in Safari, tap the <strong>Share</strong> icon, and choose <strong>Add to Home Screen</strong> for a fullscreen app icon.</div>
          </li>
          <li>
            <span class="step-dot">02</span>
            <div><strong>Native .IPA Sideload (Optional):</strong> Tap <strong>.IPA</strong> on any card (or visit <a href="https://github.com/Milanista86/craft-ipad-apps/releases/tag/v1.0.0" target="_blank" rel="noopener noreferrer" style="text-decoration: underline;">GitHub Releases</a>) to install with Feather, ESign, SideStore, or Sideloadly.</div>
          </li>
          <li>
            <span class="step-dot">03</span>
            <div><strong>Automatic Weekly Updates:</strong> Synced every Sunday from <a href="https://github.com/storytold" target="_blank" rel="noopener noreferrer" style="text-decoration: underline;">@storytold</a>. Tap <strong>⚙️ &rarr; 🔄</strong> inside any app to pull the latest version on demand.</div>
          </li>
        </ul>
      </div>

      <div class="info-card">
        <div class="info-card-head">
          <h3>iPadOS Touch &amp; Desktop Controls</h3>
          <span class="badge-community">Zero Desktop Interference</span>
        </div>
        <ul class="info-list">
          <li>
            <span class="step-dot">✦</span>
            <div><strong>100% Desktop Mouse &amp; Keyboard:</strong> Magic Keyboard, trackpad, hover states, right-click, and shortcuts work identically to macOS and Windows.</div>
          </li>
          <li>
            <span class="step-dot">✦</span>
            <div><strong>Draggable Tool Dock (⚙️) &amp; Gestures:</strong> Use <strong>2-finger tap</strong> for Undo, <strong>3-finger tap</strong> for Redo, <strong>2-finger pinch</strong> to zoom, or tap the draggable <strong>⚙️</strong> pill for quick actions.</div>
          </li>
          <li>
            <span class="step-dot">✦</span>
            <div><strong>Native iPadOS Files Integration:</strong> Exporting files automatically opens the native iPadOS <strong>Save to Files / Share Sheet</strong> (iCloud Drive, On My iPad, AirDrop).</div>
          </li>
        </ul>
      </div>
    </section>

    <!-- Clean Attribution Footer -->
    <footer class="site-footer">
      <div>
        Unofficial, non-commercial iPadOS adaptation by <a href="https://github.com/Milanista86/craft-ipad-apps" target="_blank" rel="noopener noreferrer">@Milanista86</a>. All 13 core applications &amp; icons are created by <a href="https://getartcraft.com" target="_blank" rel="noopener noreferrer">ArtCraft (@storytold)</a> (MIT / Apache-2.0).
      </div>
      <div class="footer-links">
        <a href="https://getartcraft.com" target="_blank" rel="noopener noreferrer">Official ArtCraft Site</a> &middot;
        <a href="https://github.com/storytold" target="_blank" rel="noopener noreferrer">@storytold GitHub</a> &middot;
        <a href="https://github.com/Milanista86/craft-ipad-apps/releases" target="_blank" rel="noopener noreferrer">Download .IPA Suite</a>
      </div>
    </footer>
  </main>

  <script>
    (function() {{
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
      var filterBtns = document.querySelectorAll('.filter-btn');
      var searchInput = document.getElementById('appSearch');
      var cards = document.querySelectorAll('.app-card');
      var emptyState = document.getElementById('emptyState');
      var activeCat = 'all';
      function applyFilter() {{
        var q = (searchInput ? searchInput.value : '').trim().toLowerCase();
        var visibleCount = 0;
        cards.forEach(function(card) {{
          var catMatch = (activeCat === 'all') || (card.getAttribute('data-cat') === activeCat);
          var searchBlob = card.getAttribute('data-search') || '';
          var searchMatch = !q || searchBlob.indexOf(q) !== -1;
          var show = catMatch && searchMatch;
          card.style.display = show ? '' : 'none';
          if (show) visibleCount++;
        }});
        if (emptyState) {{
          emptyState.style.display = (visibleCount === 0) ? 'block' : 'none';
        }}
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
