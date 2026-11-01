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
from PIL import Image

APPS = [
    # Creative & Design Suite
    {
        "id": "photocraft",
        "name": "PhotoCraft",
        "category": "Creative & Design",
        "equiv": "Adobe Photoshop Alternative",
        "desc": "Layered raster photo editing, PSD/PSB support, adjustment layers, masks, and brushes.",
        "fallback_bg": (47, 123, 245),
    },
    {
        "id": "vectorcraft",
        "name": "VectorCraft",
        "category": "Creative & Design",
        "equiv": "Adobe Illustrator Alternative",
        "desc": "Precision vector illustration, bezier pen workflows, boolean path operations, and SVG/PDF export.",
        "fallback_bg": (234, 88, 12),
    },
    {
        "id": "designcraft",
        "name": "DesignCraft",
        "category": "Creative & Design",
        "equiv": "Adobe InDesign Alternative",
        "desc": "Multi-page desktop publishing, master pages, typography grids, and print-ready layout design.",
        "fallback_bg": (219, 39, 119),
    },
    {
        "id": "lightcraft",
        "name": "LightCraft",
        "category": "Creative & Design",
        "equiv": "Adobe Lightroom Alternative",
        "desc": "Non-destructive RAW photo development, color grading, tone curves, and photo catalog management.",
        "fallback_bg": (14, 116, 144),
    },
    {
        "id": "filmcraft",
        "name": "FilmCraft",
        "category": "Creative & Design",
        "equiv": "Adobe Premiere Pro Alternative",
        "desc": "Nonlinear multi-track video editing, timeline trimming, transitions, and color workflows.",
        "fallback_bg": (124, 58, 237),
    },
    {
        "id": "effectcraft",
        "name": "EffectCraft",
        "category": "Creative & Design",
        "equiv": "Adobe After Effects Alternative",
        "desc": "Keyframe motion graphics, node/layer compositing, visual effects, and procedural animation.",
        "fallback_bg": (79, 70, 229),
    },
    {
        "id": "figcraft",
        "name": "FigCraft",
        "category": "Creative & Design",
        "equiv": "Figma Alternative",
        "desc": "Infinite-canvas interface design, auto-layout frames, component systems, and interactive prototyping.",
        "fallback_bg": (16, 185, 129),
    },
    # Office, Audio & Engineering Suite
    {
        "id": "wordcraft",
        "name": "WordCraft",
        "category": "Office, Audio & Engineering",
        "equiv": "Microsoft Word Alternative",
        "desc": "Full Ribbon word processor with paginated layout, styles, tables, and native DOCX/ODT/RTF support.",
        "fallback_bg": (59, 91, 219),
    },
    {
        "id": "gridcraft",
        "name": "GridCraft",
        "category": "Office, Audio & Engineering",
        "equiv": "Microsoft Excel Alternative",
        "desc": "High-speed spreadsheet engine with formulas, pivot tables, charts, and XLSX/CSV support.",
        "fallback_bg": (22, 163, 74),
    },
    {
        "id": "deckcraft",
        "name": "DeckCraft",
        "category": "Office, Audio & Engineering",
        "equiv": "Microsoft PowerPoint Alternative",
        "desc": "Slide deck authoring, master templates, speaker notes, animations, and PPTX presentation support.",
        "fallback_bg": (217, 119, 6),
    },
    {
        "id": "pdfcraft",
        "name": "PdfCraft",
        "category": "Office, Audio & Engineering",
        "equiv": "Adobe Acrobat Pro Alternative",
        "desc": "PDF reader, page organizer, merger/splitter, interactive form filler, and annotation workbench.",
        "fallback_bg": (183, 2, 40),
    },
    {
        "id": "soundcraft",
        "name": "SoundCraft",
        "category": "Office, Audio & Engineering",
        "equiv": "Avid Pro Tools Alternative",
        "desc": "Digital audio workstation (DAW) for multitrack recording, waveform editing, mixing, and mastering.",
        "fallback_bg": (13, 148, 136),
    },
    {
        "id": "cadcraft",
        "name": "CADCraft",
        "category": "Office, Audio & Engineering",
        "equiv": "AutoCAD Alternative",
        "desc": "Precision 2D/3D computer-aided design, technical drafting, dimensioning, and DXF/DWG workflows.",
        "fallback_bg": (220, 38, 38),
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
    creative_cards = []
    office_cards = []

    for app in APPS:
        card_html = f"""      <div class="card">
        <img class="icon" src="./{app['id']}/icon.png?v=4" alt="{app['name']}" loading="lazy">
        <span class="equiv">{app['equiv']}</span>
        <h2>{app['name']}</h2>
        <p>{app['desc']}</p>
        <a class="btn btn-primary" href="./{app['id']}/?v=4">Launch {app['name']}</a>
        <div class="sub-links">
          <a href="https://github.com/Milanista86/craft-ipad-apps/releases/download/v1.0.0/{app['name']}-iPad.ipa">Download .ipa</a>
          <span>&middot;</span>
          <a href="https://github.com/storytold/{app['id']}" target="_blank">Source Repo</a>
        </div>
      </div>"""
        if app["category"] == "Creative & Design":
            creative_cards.append(card_html)
        else:
            office_cards.append(card_html)

    creative_section = "\n".join(creative_cards)
    office_section = "\n".join(office_cards)

    hub_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>ArtCraft Suite for iPadOS — Complete 13-App Desktop Suite</title>
  <style>
    :root {{ color-scheme: dark; }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; padding: 48px 24px 64px;
      background: radial-gradient(circle at top, #172036 0%, #0b0d14 60%);
      color: #f3f4f6;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
      display: flex; flex-direction: column; align-items: center; min-height: 100vh;
    }}
    .container {{ max-width: 1120px; width: 100%; }}
    .header {{ text-align: center; margin-bottom: 42px; }}
    .badge {{
      display: inline-block;
      background: rgba(59, 130, 246, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.38);
      color: #60a5fa;
      font-size: 13px; font-weight: 600;
      padding: 6px 14px; border-radius: 999px;
      margin-bottom: 14px; text-decoration: none;
    }}
    h1 {{ font-size: 38px; font-weight: 800; margin: 0 0 12px; letter-spacing: -0.02em; }}
    .subtitle {{
      color: #9ca3af; font-size: 16px; line-height: 1.6;
      margin: 0 auto; max-width: 740px;
    }}
    .subtitle a {{ color: #60a5fa; text-decoration: none; font-weight: 600; }}
    .section-title {{
      font-size: 22px; font-weight: 700; color: #e5e7eb;
      margin: 32px 0 16px; padding-bottom: 10px;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      display: flex; align-items: center; justify-content: space-between;
    }}
    .section-title span {{ font-size: 13px; font-weight: 500; color: #9ca3af; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 18px; margin-bottom: 28px;
    }}
    .card {{
      background: rgba(24, 27, 36, 0.92);
      border: 1px solid rgba(255,255,255,0.09);
      border-radius: 22px; padding: 24px 20px 18px;
      display: flex; flex-direction: column; align-items: center; text-align: center;
      box-shadow: 0 12px 32px rgba(0,0,0,0.4);
      transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .card:hover {{ border-color: rgba(96, 165, 250, 0.4); transform: translateY(-2px); }}
    .icon {{
      width: 88px; height: 88px; border-radius: 20px; margin-bottom: 12px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.45);
    }}
    .equiv {{
      font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
      color: #60a5fa; background: rgba(59, 130, 246, 0.12);
      padding: 4px 10px; border-radius: 999px; margin-bottom: 8px;
    }}
    .card h2 {{ margin: 0 0 8px; font-size: 21px; }}
    .card p {{ margin: 0 0 18px; color: #9ca3af; font-size: 13.5px; line-height: 1.45; flex: 1; }}
    .btn {{
      display: block; width: 100%; padding: 12px 16px; border-radius: 12px;
      font-weight: 600; font-size: 14.5px; text-decoration: none; margin-bottom: 10px;
    }}
    .btn-primary {{ background: #0a84ff; color: #ffffff; }}
    .sub-links {{ font-size: 12.5px; color: #6b7280; display: flex; gap: 8px; align-items: center; }}
    .sub-links a {{ color: #9ca3af; text-decoration: none; }}
    .sub-links a:hover {{ color: #f3f4f6; text-decoration: underline; }}
    .panel {{
      background: rgba(24, 27, 36, 0.88);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 20px; padding: 24px 28px; margin-top: 12px; margin-bottom: 24px;
    }}
    .panel h3 {{ margin: 0 0 12px; font-size: 18px; color: #60a5fa; }}
    .panel ol {{ margin: 0; padding-left: 20px; color: #d1d5db; line-height: 1.75; font-size: 15px; }}
    .footer {{ text-align: center; color: #6b7280; font-size: 13px; margin-top: 16px; }}
    .footer a {{ color: #9ca3af; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <a class="badge" href="https://github.com/storytold" target="_blank">Complete 13-App Suite &middot; Powered by ArtCraft (@storytold)</a>
      <h1>ArtCraft Suite for iPadOS</h1>
      <p class="subtitle">
        Run all 13 desktop Rust creative, office, audio, and CAD applications from <a href="https://github.com/storytold" target="_blank">github.com/storytold</a> natively on any modern iPad — complete with official icons, iPadOS Status Bar safe-area layout, Touch/Apple Pencil Right-Click &amp; Keyboard tools, and native iPadOS Files support.
      </p>
    </div>

    <div class="section-title">
      <div>Creative &amp; Design Suite</div>
      <span>7 Desktop Applications</span>
    </div>
    <div class="grid">
{creative_section}
    </div>

    <div class="section-title">
      <div>Office, Audio &amp; Engineering Suite</div>
      <span>6 Desktop Applications</span>
    </div>
    <div class="grid">
{office_section}
    </div>

    <div class="panel">
      <h3>How to Install Any App onto Your iPad Home Screen (No PC Required):</h3>
      <ol>
        <li>Open this page in <strong>Safari</strong> on your iPad (compatible with iPad, iPad Air, iPad mini, and iPad Pro).</li>
        <li>Tap <strong>Launch</strong> on any of the 13 applications above and wait a couple of seconds for it to load.</li>
        <li>Tap the <strong>Share</strong> button at the top-right of Safari and select <strong>Add to Home Screen</strong>.</li>
        <li>Tap <strong>Add</strong> to install the fullscreen standalone app with its official icon directly onto your iPad Home Screen!</li>
      </ol>
    </div>

    <div class="footer">
      <a href="https://github.com/Milanista86/craft-ipad-apps">GitHub Repository &amp; Documentation</a> &middot;
      <a href="https://github.com/Milanista86/craft-ipad-apps/releases">All 13 Native .ipa Downloads</a> &middot;
      Upstream engines &amp; artwork by <a href="https://github.com/storytold">storytold</a> (MIT / Apache-2.0)
    </div>
  </div>
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
