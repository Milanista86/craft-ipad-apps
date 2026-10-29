# ArtCraft Suite for iPadOS

<p align="center">
  <img src="https://milanista86.github.io/craft-ipad-apps/photocraft/icon.png" width="88" alt="PhotoCraft Icon" style="border-radius: 20px; margin: 0 10px;" />
  <img src="https://milanista86.github.io/craft-ipad-apps/wordcraft/icon.png" width="88" alt="WordCraft Icon" style="border-radius: 20px; margin: 0 10px;" />
  <img src="https://milanista86.github.io/craft-ipad-apps/pdfcraft/icon.png" width="88" alt="PdfCraft Icon" style="border-radius: 20px; margin: 0 10px;" />
</p>

<p align="center">
  <strong>Universal iPadOS Adaptation &amp; Cloud Builder for the <a href="https://github.com/storytold">ArtCraft (@storytold)</a> Application Ecosystem</strong><br>
  Run the full desktop Rust + WebGPU/WebGL2 creative and productivity apps natively on any modern iPad.
</p>

<p align="center">
  <a href="https://milanista86.github.io/craft-ipad-apps/"><strong>🚀 Open Live iPad App Hub</strong></a> ·
  <a href="https://github.com/Milanista86/craft-ipad-apps/releases"><strong>📦 Download .ipa Releases</strong></a> ·
  <a href="https://github.com/storytold"><strong>✨ Original ArtCraft Repositories (@storytold)</strong></a>
</p>

---

## About This Project

The **[ArtCraft Suite](https://github.com/storytold)** (created by `@storytold`) is an acclaimed open-source family of clean-room desktop creative and office applications written from scratch in pure Rust (`egui` + `eframe` + `wgpu`). While the official repositories provide native builds for Windows, macOS, Linux, and FreeBSD alongside web bundles, running the full desktop interfaces directly on **iPadOS** faces several hurdles out of the box—such as the iPadOS Status Bar covering the top menu bar, lack of touch right-click and virtual keyboard triggers, and no native `.ipa` wrapper.

**ArtCraft Suite for iPadOS** provides a universal, reusable adaptation layer and automated GitHub Actions pipeline that makes **any application from the [ArtCraft (@storytold)](https://github.com/storytold) organization** work seamlessly as a full-screen desktop application on **any modern iPad** (iPad, iPad Air, iPad mini, and iPad Pro across Apple M-series and A-series chips).

---

## Currently Hosted Apps (Live Now)

While this architecture supports the **entire ArtCraft ecosystem**, this repository currently builds, hosts, and auto-updates three core applications out of the box:

| Application | Original Upstream Repo | Desktop Equivalent | Live iPad Web App | Native `.ipa` |
| :--- | :--- | :--- | :--- | :--- |
| **PhotoCraft** | [`storytold/photocraft`](https://github.com/storytold/photocraft) | Layered Photo & `.psd` Editor | [**Launch PhotoCraft**](https://milanista86.github.io/craft-ipad-apps/photocraft/) | [Download `.ipa`](https://github.com/Milanista86/craft-ipad-apps/releases/download/v1.0.0/PhotoCraft-iPad.ipa) |
| **WordCraft** | [`storytold/wordcraft`](https://github.com/storytold/wordcraft) | Word Processor (`.docx`, `.odt`, `.rtf`) | [**Launch WordCraft**](https://milanista86.github.io/craft-ipad-apps/wordcraft/) | [Download `.ipa`](https://github.com/Milanista86/craft-ipad-apps/releases/download/v1.0.0/WordCraft-iPad.ipa) |
| **PdfCraft** | [`storytold/pdfcraft`](https://github.com/storytold/pdfcraft) | PDF Reader, Organizer & Editor | [**Launch PdfCraft**](https://milanista86.github.io/craft-ipad-apps/pdfcraft/) | [Download `.ipa`](https://github.com/Milanista86/craft-ipad-apps/releases/download/v1.0.0/PdfCraft-iPad.ipa) |

---

## Compatible With the Entire ArtCraft Ecosystem

Because every application in the **[storytold](https://github.com/storytold)** organization shares the same `egui` / `eframe` + `wgpu` + WebAssembly architecture, **this exact wrapper and cloud pipeline works with all ArtCraft apps**, including:

* 🎨 **[VectorCraft](https://github.com/storytold/vectorcraft)** — Vector illustration workbench
* 📊 **[GridCraft](https://github.com/storytold/gridcraft)** — Spreadsheet & data engine
* 📽️ **[DeckCraft](https://github.com/storytold/deckcraft)** — Presentation & slide studio
* 🎬 **[FilmCraft](https://github.com/storytold/filmcraft)** — Non-linear video editing
* 📸 **[LightCraft](https://github.com/storytold/lightcraft)** — RAW photo development & catalog
* 📐 **[DesignCraft](https://github.com/storytold/designcraft)** — Multi-page desktop publishing & layout
* ✨ **[EffectCraft](https://github.com/storytold/effectcraft)** — Motion graphics & compositing
* 🔊 **[SoundCraft](https://github.com/storytold/soundcraft)** — Digital audio workstation & editing

### How to Add Any Other ArtCraft App
To add another app from `github.com/storytold` to your iPad hub:
1. Add its repository name (e.g., `vectorcraft`, `gridcraft`, `deckcraft`) to the matrix in [`.github/workflows/build-ipad-apps.yml`](.github/workflows/build-ipad-apps.yml) and the loop in [`.github/workflows/auto-update-cloud.yml`](.github/workflows/auto-update-cloud.yml).
2. Trigger the workflow under the **Actions** tab—GitHub Actions will automatically package the WebAssembly engine, official icon, and iPadOS bridge for you.

---

## What This iPadOS Adaptation Adds

1. **iPadOS Status Bar Safe-Area Offset:** Pushes the application viewport below the iPadOS Status Bar and multitasking window handle (`--ipad-status-offset: max(env(safe-area-inset-top, 0px), 26px)`) so top menu bars (`File`, `Edit`, `Image`, `Layer`, `View`, `Help`) are never blocked and remain 100% clickable.
2. **Floating Touch & Apple Pencil Helper (`⚙️`):** Adds a sleek, collapsible floating pill in the bottom-right corner with:
   * **`Right-Click`:** Tap to arm right-click mode, then touch anywhere on the canvas with your finger or Apple Pencil to open desktop context menus when no mouse/trackpad is connected.
   * **`⌨️` (Keyboard):** Summon the native iPadOS on-screen keyboard on demand.
   * **`🔄` (Reload):** One-tap refresh to pull the latest upstream version directly inside the fullscreen Home Screen app.
3. **Native iPadOS Files Integration:** Opening and saving/exporting files connects directly to the native **iPadOS Files** app (`On My iPad`, `iCloud Drive`, and external USB-C storage).
4. **Official Full-Bleed App Icons:** Automatically formats `storytold`'s official `1024x1024` app icons edge-to-edge for iPadOS Home Screen squircle masking.

---

## Installation Guide (Works on Any Modern iPad)

### Method 1: Instant Cloud Install via Safari (Recommended — No PC Required)
1. Open **[https://milanista86.github.io/craft-ipad-apps/](https://milanista86.github.io/craft-ipad-apps/)** in **Safari** on your iPad.
2. Tap **Open PhotoCraft**, **Open WordCraft**, or **Open PdfCraft** and wait a couple of seconds for the app to load.
3. Tap the **Share** button in Safari (the square with an arrow pointing up) and select **Add to Home Screen**.
4. Tap **Add**. The app is now installed on your iPad Home Screen with its official icon and runs **100% fullscreen** without Safari bars.

### Method 2: Native `.ipa` Sideloading (Apple Developer Account)
If you prefer installing the native Swift + `WKWebView` + `NWListener` `.ipa` packages (`PhotoCraft-iPad.ipa`, `WordCraft-iPad.ipa`, `PdfCraft-iPad.ipa`):
1. Download the `.ipa` files from the [**Releases**](https://github.com/Milanista86/craft-ipad-apps/releases) page.
2. Sign and install them onto your iPad using [Sideloadly](https://sideloadly.io/), AltStore, Feather, or Xcode.

---

## Automatic Upstream Updates

An automated GitHub Actions workflow ([`.github/workflows/auto-update-cloud.yml`](.github/workflows/auto-update-cloud.yml)) runs weekly (and on manual 1-click trigger from the **Actions** tab) to fetch the newest releases from [`github.com/storytold`](https://github.com/storytold), apply the iPadOS layout and touch patches, and publish them directly to GitHub Pages.

---

## Credits & License

* All core applications (`PhotoCraft`, `WordCraft`, `PdfCraft`, and sibling Craft apps) and official artwork are created by **[storytold (ArtCraft)](https://github.com/storytold)**.
* Licensed under **MIT** / **Apache-2.0**, matching the upstream repositories.
