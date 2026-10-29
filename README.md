# Craft Suite for iPadOS

<p align="center">
  <img src="https://milanista86.github.io/craft-ipad-apps/photocraft/icon.png" width="84" alt="PhotoCraft Icon" style="border-radius: 18px; margin: 0 8px;" />
  <img src="https://milanista86.github.io/craft-ipad-apps/wordcraft/icon.png" width="84" alt="WordCraft Icon" style="border-radius: 18px; margin: 0 8px;" />
  <img src="https://milanista86.github.io/craft-ipad-apps/pdfcraft/icon.png" width="84" alt="PdfCraft Icon" style="border-radius: 18px; margin: 0 8px;" />
</p>

<p align="center">
  <strong>Full Desktop PhotoCraft, WordCraft, and PdfCraft — Adapted for iPadOS</strong><br>
  Run the complete desktop Rust + WebGPU/WebGL2 creative and office suite from <a href="https://github.com/storytold">storytold</a> natively on any modern iPad.
</p>

<p align="center">
  <a href="https://milanista86.github.io/craft-ipad-apps/"><strong>🚀 Launch iPad Web App Hub</strong></a> ·
  <a href="https://github.com/Milanista86/craft-ipad-apps/releases"><strong>📦 Download .ipa Releases</strong></a> ·
  <a href="https://github.com/storytold"><strong>✨ Upstream Repositories</strong></a>
</p>

---

## Overview

The **[storytold](https://github.com/storytold)** project provides clean-room, open-source desktop applications written in pure Rust (`egui` + `eframe` + `wgpu`). While upstream releases target Windows, macOS, Linux, FreeBSD, and desktop browsers, iPad users normally face mobile viewport issues, iPadOS status bar overlaps, missing right-click/keyboard bridges, and lack of standalone `.ipa` or Home Screen packaging.

**Craft Suite for iPadOS** bridges that gap for **all modern iPads** (iPad, iPad Air, iPad mini, and iPad Pro across Apple M-series and A-series chips running iPadOS 15+):

| Application | Upstream Repo | Description | Live iPad App |
| :--- | :--- | :--- | :--- |
| **PhotoCraft** | [`storytold/photocraft`](https://github.com/storytold/photocraft) | Layered raster image & `.psd` editor | [Open PhotoCraft](https://milanista86.github.io/craft-ipad-apps/photocraft/) |
| **WordCraft** | [`storytold/wordcraft`](https://github.com/storytold/wordcraft) | Ribbon-based word processor (`.docx`, `.odt`, `.rtf`) | [Open WordCraft](https://milanista86.github.io/craft-ipad-apps/wordcraft/) |
| **PdfCraft** | [`storytold/pdfcraft`](https://github.com/storytold/pdfcraft) | PDF reader, page organizer, form & annotation workbench | [Open PdfCraft](https://milanista86.github.io/craft-ipad-apps/pdfcraft/) |

---

## Key iPadOS Enhancements

* **iPadOS Status Bar Safe-Area Layout:** Automatically offsets the application canvas below the iPadOS Status Bar and multitasking window controls so top menu bars (`File`, `Edit`, `Image`, `Layer`, `View`, etc.) are 100% accessible.
* **Floating Touch & Apple Pencil Helper (`⚙️`):** Includes a collapsible corner tool pill providing:
  * **Right-Click Toggle:** Tap `Right-Click` then touch anywhere on the canvas with your finger or Apple Pencil to trigger desktop context menus when using the iPad without a trackpad or mouse.
  * **On-Screen Keyboard Trigger (`⌨️`):** Summon the native iPadOS software keyboard on demand when no hardware keyboard is attached.
  * **One-Tap Reload (`🔄`):** Refresh and pull the latest upstream release directly inside the fullscreen Home Screen app.
* **Native iPadOS Files Integration:** Opening and saving/exporting documents connects directly to the native **iPadOS Files** picker (`On My iPad`, `iCloud Drive`, and external USB-C drives).
* **Official Full-Bleed App Icons:** Pre-configured with `storytold`'s official artwork formatted for iPadOS Home Screen squircle masking.
* **Two Installation Modes:**
  1. **Zero-PC Cloud Install (Recommended):** Add directly to your iPad Home Screen from Safari via GitHub Pages.
  2. **Standalone `.ipa` Sideload:** Native Swift + `WKWebView` + loopback server (`NWListener`) `.ipa` bundles built automatically via GitHub Actions.

---

## Option 1: Instant iPad Home Screen Install (No Computer Required)

Works on **any iPad running iPadOS 15 or newer**:

1. Open **[https://milanista86.github.io/craft-ipad-apps/](https://milanista86.github.io/craft-ipad-apps/)** in **Safari** on your iPad.
2. Tap **Open PhotoCraft**, **Open WordCraft**, or **Open PdfCraft** and wait a few seconds for the page to load.
3. Tap the **Share** button in Safari (the square with an upward arrow) and select **Add to Home Screen**.
4. Tap **Add**. Each app will appear on your iPad Home Screen with its official icon and launch **100% fullscreen** without browser toolbars.

---

## Option 2: Sideloading the Native `.ipa` Files

If you prefer installing the standalone native iPadOS `.ipa` wrapper using an Apple Developer account (via [Sideloadly](https://sideloadly.io/), AltStore, Feather, or Xcode):

1. Download **`PhotoCraft-iPad.ipa`**, **`WordCraft-iPad.ipa`**, and **`PdfCraft-iPad.ipa`** from the [**Releases**](https://github.com/Milanista86/craft-ipad-apps/releases) page (or from the latest [GitHub Actions](https://github.com/Milanista86/craft-ipad-apps/actions) run).
2. Sign and install each `.ipa` onto your iPad using your preferred sideloading tool.
3. Because each app uses a distinct Bundle Identifier (`com.craftsuite.photocraft`, `com.craftsuite.wordcraft`, `com.craftsuite.pdfcraft`), all three install side-by-side.

---

## Repository Structure

```text
├── .github/workflows/
│   ├── build-ipad-apps.yml     # Cloud macOS Xcode builder producing unsigned .ipa bundles
│   └── auto-update-cloud.yml   # Automated weekly & on-demand updater for GitHub Pages
├── ios-wrapper/                # Native Swift iPadOS wrapper (XcodeGen project)
│   ├── project.yml             # XcodeGen specification
│   └── Sources/
│       ├── AppDelegate.swift           # UIKit application lifecycle
│       ├── CraftWebViewController.swift# Fullscreen WKWebView + Files export & touch bridge
│       ├── LocalAssetServer.swift      # Offline 127.0.0.1 HTTP server (Network.framework)
│       └── Info.plist                  # iPadOS orientations, Split View & Stage Manager config
└── README.md
```

---

## Automatic Updates

This repository includes an automated workflow ([`.github/workflows/auto-update-cloud.yml`](.github/workflows/auto-update-cloud.yml)) that checks [`storytold/photocraft`](https://github.com/storytold/photocraft), [`storytold/wordcraft`](https://github.com/storytold/wordcraft), and [`storytold/pdfcraft`](https://github.com/storytold/pdfcraft) every week (and on manual trigger via the **Actions** tab) to keep the iPad builds synchronized with the latest upstream releases.

---

## Privacy & Security

* **100% Local Execution:** All image editing, word processing, and PDF rendering run locally on your iPad's CPU/GPU via WebAssembly and WebGPU/WebGL2.
* **No Cloud Uploads or Telemetry:** Your documents and images never leave your device.

---

## Credits & License

* Core applications (`PhotoCraft`, `WordCraft`, `PdfCraft`) and official icons are created and maintained by **[storytold](https://github.com/storytold)** ([ArtCraft Suite](https://getartcraft.com/)).
* Upstream engines and this iPadOS adaptation are dual-licensed under the **MIT** or **Apache-2.0** licenses.
