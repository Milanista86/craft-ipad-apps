import UIKit
import WebKit
import UniformTypeIdentifiers

final class CraftWebViewController: UIViewController, WKScriptMessageHandler, WKUIDelegate, WKNavigationDelegate {
    private var webView: WKWebView!
    private var server: LocalAssetServer?

    override var prefersStatusBarHidden: Bool {
        return true
    }

    override var preferredScreenEdgesDeferringSystemGestures: UIRectEdge {
        return [.all]
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor(red: 0.11, green: 0.11, blue: 0.12, alpha: 1.0)
        setupWebView()
        startLocalServerAndLoad()
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        setNeedsStatusBarAppearanceUpdate()
        setNeedsUpdateOfScreenEdgesDeferringSystemGestures()
    }

    private func setupWebView() {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []
        config.defaultWebpagePreferences.preferredContentMode = .desktop

        let contentController = WKUserContentController()
        contentController.add(self, name: "craftSaveFile")

        let bridgeScript = WKUserScript(
            source: Self.injectedDesktopBridgeJS,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        )
        contentController.addUserScript(bridgeScript)
        config.userContentController = contentController

        // Enable full desktop storage & WebGL/WebGPU acceleration
        config.websiteDataStore = .default()

        webView = WKWebView(frame: view.bounds, configuration: config)
        webView.translatesAutoresizingMaskIntoConstraints = false
        webView.uiDelegate = self
        webView.navigationDelegate = self
        webView.isOpaque = false
        webView.backgroundColor = view.backgroundColor
        webView.scrollView.backgroundColor = view.backgroundColor
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.scrollView.bounces = false
        webView.scrollView.alwaysBounceVertical = false
        webView.scrollView.alwaysBounceHorizontal = false
        webView.scrollView.isScrollEnabled = false
        webView.scrollView.pinchGestureRecognizer?.isEnabled = false

        // Present as Desktop macOS Safari so eframe/egui uses full desktop layout & shortcuts
        webView.customUserAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"

        view.addSubview(webView)
        NSLayoutConstraint.activate([
            webView.topAnchor.constraint(equalTo: view.topAnchor),
            webView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            webView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            webView.trailingAnchor.constraint(equalTo: view.trailingAnchor)
        ])
    }

    private func startLocalServerAndLoad() {
        guard let wwwURL = Bundle.main.url(forResource: "www", withExtension: nil) else {
            showError("Missing bundled 'www' directory inside the app bundle.")
            return
        }

        // Use a deterministic preferred port per app bundle so IndexedDB/localStorage persists across launches
        let bundleHash = abs((Bundle.main.bundleIdentifier ?? "craft").hashValue)
        let preferredPort = UInt16(18000 + (bundleHash % 1000))

        let localServer = LocalAssetServer(rootDirectory: wwwURL)
        self.server = localServer

        localServer.start(preferredPort: preferredPort) { [weak self] result in
            switch result {
            case .success(let port):
                if let url = URL(string: "http://127.0.0.1:\(port)/index.html") {
                    let request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData)
                    self?.webView.load(request)
                }
            case .failure(let error):
                self?.showError("Failed to start local Wasm server: \(error.localizedDescription)")
            }
        }
    }

    // MARK: - Native File Export Bridge (Save to iPadOS Files App)

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "craftSaveFile",
              let body = message.body as? [String: Any],
              let filename = body["filename"] as? String,
              let base64 = body["base64"] as? String,
              let fileData = Data(base64Encoded: base64, options: .ignoreUnknownCharacters) else {
            return
        }

        let safeName = filename.isEmpty ? "Untitled" : (filename as NSString).lastPathComponent
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(safeName)

        do {
            try fileData.write(to: tempURL, options: .atomic)
            let picker = UIDocumentPickerViewController(forExporting: [tempURL], asCopy: true)
            picker.modalPresentationStyle = .formSheet
            present(picker, animated: true)
        } catch {
            showError("Could not save file: \(error.localizedDescription)")
        }
    }

    // MARK: - WKUIDelegate (Native JS Alerts / Confirmations)

    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler() })
        present(alert, animated: true)
    }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in completionHandler(false) })
        alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(true) })
        present(alert, animated: true)
    }

    private func showError(_ text: String) {
        DispatchQueue.main.async {
            let alert = UIAlertController(title: "Craft iPad Wrapper", message: text, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "OK", style: .default))
            self.present(alert, animated: true)
        }
    }

    // MARK: - Injected iPadOS Desktop Bridge (File Saving + Touch/Pencil Ergonomics)

    private static let injectedDesktopBridgeJS = #"""
    (function() {
        // 1. Helper to convert a Blob to Base64 and send to Swift's UIDocumentPickerViewController
        function sendBlobToNativeFiles(blob, filename) {
            const reader = new FileReader();
            reader.onloadend = function() {
                const dataUrl = reader.result || "";
                const commaIndex = dataUrl.indexOf(",");
                const base64 = commaIndex >= 0 ? dataUrl.substring(commaIndex + 1) : dataUrl;
                if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.craftSaveFile) {
                    window.webkit.messageHandlers.craftSaveFile.postMessage({
                        filename: filename || "download",
                        base64: base64
                    });
                }
            };
            reader.readAsDataURL(blob);
        }

        // 2. Intercept <a download="filename" href="blob:..."> clicks used by rfd / eframe on WebAssembly
        const originalClick = HTMLAnchorElement.prototype.click;
        HTMLAnchorElement.prototype.click = function() {
            const hasDownload = this.hasAttribute("download") || Boolean(this.download);
            const href = this.href || "";
            if (hasDownload && (href.startsWith("blob:") || href.startsWith("data:"))) {
                const fname = this.getAttribute("download") || this.download || "document";
                fetch(href)
                    .then(r => r.blob())
                    .then(blob => sendBlobToNativeFiles(blob, fname))
                    .catch(() => originalClick.apply(this, arguments));
                return;
            }
            return originalClick.apply(this, arguments);
        };

        // 3. Polyfill window.showSaveFilePicker so apps using File System Access API save cleanly to iPadOS Files
        if (!window.showSaveFilePicker) {
            window.showSaveFilePicker = async function(options) {
                const suggestedName = (options && options.suggestedName) ? options.suggestedName : "document";
                return {
                    name: suggestedName,
                    createWritable: async function() {
                        const chunks = [];
                        return {
                            write: async function(data) {
                                if (data && data.data) {
                                    chunks.push(data.data);
                                } else {
                                    chunks.push(data);
                                }
                            },
                            close: async function() {
                                const blob = new Blob(chunks);
                                sendBlobToNativeFiles(blob, suggestedName);
                            }
                        };
                    }
                };
            };
        }

        // 4. Lock viewport & add optional floating Touch Helper for right-click & on-screen keyboard
        window.addEventListener("DOMContentLoaded", function() {
            let meta = document.querySelector('meta[name="viewport"]');
            if (!meta) {
                meta = document.createElement("meta");
                meta.name = "viewport";
                document.head.appendChild(meta);
            }
            meta.content = "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover";

            const style = document.createElement("style");
            style.textContent = `
                html, body, canvas {
                    overscroll-behavior: none !important;
                    -webkit-touch-callout: none !important;
                    -webkit-user-select: none !important;
                    user-select: none !important;
                    touch-action: none !important;
                }
                #craft-ipad-helper {
                    position: fixed;
                    right: 12px;
                    bottom: 12px;
                    z-index: 2147483647;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    background: rgba(24, 24, 28, 0.82);
                    backdrop-filter: blur(10px);
                    -webkit-backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.16);
                    border-radius: 999px;
                    padding: 4px 8px;
                    font: 600 12px/1 -apple-system, BlinkMacSystemFont, sans-serif;
                    color: #f0f0f5;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.35);
                }
                #craft-ipad-helper.collapsed .helper-btn {
                    display: none;
                }
                #craft-ipad-helper button {
                    appearance: none;
                    border: none;
                    background: rgba(255, 255, 255, 0.1);
                    color: #f0f0f5;
                    padding: 5px 9px;
                    border-radius: 999px;
                    font: inherit;
                    cursor: pointer;
                }
                #craft-ipad-helper button.active {
                    background: #0a84ff;
                    color: #fff;
                }
            `;
            document.head.appendChild(style);

            if (document.getElementById("craft-ipad-helper")) return;

            const toast = document.createElement("div");
            toast.id = "craft-ipad-toast";
            toast.style.cssText = "position:fixed;top:34px;left:50%;transform:translateX(-50%);z-index:2147483647;background:rgba(20,20,24,0.88);color:#fff;border:1px solid rgba(255,255,255,0.16);border-radius:999px;padding:6px 14px;font:600 12px/1 -apple-system,BlinkMacSystemFont,sans-serif;pointer-events:none;opacity:0;transition:opacity 0.15s ease;box-shadow:0 4px 12px rgba(0,0,0,0.35);";
            document.body.appendChild(toast);
            let toastTimer = null;
            function showToast(text) {
                toast.textContent = text;
                toast.style.opacity = "1";
                if (toastTimer) clearTimeout(toastTimer);
                toastTimer = setTimeout(function() { toast.style.opacity = "0"; }, 650);
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

            let isRightClickArmed = false;
            const bar = document.createElement("div");
            bar.id = "craft-ipad-helper";
            bar.className = "collapsed";
            bar.innerHTML = `
                <button id="craft-undo-btn" class="helper-btn" title="Undo (Ctrl+Z)">↩️</button>
                <button id="craft-redo-btn" class="helper-btn" title="Redo (Ctrl+Y)">↪️</button>
                <button id="craft-del-btn" class="helper-btn" title="Delete Selected">⌫</button>
                <button id="craft-rc-btn" class="helper-btn" title="Tap then touch canvas to Right-Click">Right-Click</button>
                <button id="craft-kb-btn" class="helper-btn" title="Toggle iPad On-Screen Keyboard">⌨️</button>
                <button id="craft-reload-btn" class="helper-btn" title="Fetch Latest Cloud Update">🔄</button>
                <button id="craft-toggle-btn" title="Tap to open tools, or drag to move">⚙️</button>
            `;
            document.body.appendChild(bar);

            const undoBtn = document.getElementById("craft-undo-btn");
            const redoBtn = document.getElementById("craft-redo-btn");
            const delBtn = document.getElementById("craft-del-btn");
            const rcBtn = document.getElementById("craft-rc-btn");
            const kbBtn = document.getElementById("craft-kb-btn");
            const reloadBtn = document.getElementById("craft-reload-btn");
            const toggleBtn = document.getElementById("craft-toggle-btn");

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
                    bar.style.left = Math.min(Math.max(6, dragStart.left + dx), window.innerWidth - rect.width - 6) + "px";
                    bar.style.top = Math.min(Math.max(6, dragStart.top + dy), window.innerHeight - rect.height - 6) + "px";
                    bar.style.right = "auto";
                    bar.style.bottom = "auto";
                }
            });
            toggleBtn.addEventListener("pointerup", function(e) {
                if (!dragStart) return;
                e.stopPropagation();
                if (!didDragPill) bar.classList.toggle("collapsed");
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
                isRightClickArmed = !isRightClickArmed;
                rcBtn.classList.toggle("active", isRightClickArmed);
                if (isRightClickArmed) showToast("Tap canvas to Right-Click");
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
                const title = (document.title || "").toLowerCase().replace(/[^a-z0-9]/g, "");
                if (navigator.onLine && title) {
                    window.location.replace("https://milanista86.github.io/craft-ipad-apps/" + title + "/?ipa=1&v=" + Date.now());
                } else {
                    window.location.reload();
                }
            });

            // Convert armed tap on canvas into a desktop right-click (button 2)
            window.addEventListener("pointerdown", function(e) {
                if (!isRightClickArmed) return;
                if (bar.contains(e.target)) return;
                isRightClickArmed = false;
                rcBtn.classList.remove("active");
                e.stopImmediatePropagation();
                e.preventDefault();

                const target = e.target;
                const opts = {
                    bubbles: true,
                    cancelable: true,
                    clientX: e.clientX,
                    clientY: e.clientY,
                    screenX: e.screenX,
                    screenY: e.screenY,
                    button: 2,
                    buttons: 2
                };
                target.dispatchEvent(new PointerEvent("pointerdown", opts));
                target.dispatchEvent(new MouseEvent("mousedown", opts));
                target.dispatchEvent(new MouseEvent("contextmenu", opts));
                target.dispatchEvent(new PointerEvent("pointerup", { ...opts, buttons: 0 }));
                target.dispatchEvent(new MouseEvent("mouseup", { ...opts, buttons: 0 }));
            }, true);

            let touchState = null;
            window.addEventListener("touchstart", function(e) {
                if (bar.contains(e.target)) return;
                const count = e.touches.length;
                if (count >= 2) {
                    const pts = [];
                    for (let i = 0; i < count; i++) pts.push({ x: e.touches[i].clientX, y: e.touches[i].clientY });
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

            window.addEventListener("touchcancel", function() { touchState = null; }, { passive: true });
        });
    })();
    """#
}
