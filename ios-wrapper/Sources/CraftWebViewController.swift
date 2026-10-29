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
        view.backgroundColor = UIColor(red: 0.12, green: 0.12, blue: 0.14, alpha: 1.0)
        setupWebView()
        startLocalServerAndLoad()
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

            let rightClickArmed = false;
            const bar = document.createElement("div");
            bar.id = "craft-ipad-helper";
            bar.className = "collapsed";
            bar.innerHTML = `
                <button id="craft-rc-btn" class="helper-btn" title="Tap then touch canvas to Right-Click">Right-Click</button>
                <button id="craft-kb-btn" class="helper-btn" title="Toggle iPad On-Screen Keyboard">⌨️</button>
                <button id="craft-toggle-btn" title="Show/Hide iPad Touch Tools">⚙️</button>
            `;
            document.body.appendChild(bar);

            const rcBtn = document.getElementById("craft-rc-btn");
            const kbBtn = document.getElementById("craft-kb-btn");
            const toggleBtn = document.getElementById("craft-toggle-btn");

            toggleBtn.addEventListener("pointerdown", function(e) {
                e.stopPropagation();
                bar.classList.toggle("collapsed");
            });

            rcBtn.addEventListener("pointerdown", function(e) {
                e.stopPropagation();
                rightClickArmed = !rightClickArmed;
                rcBtn.classList.toggle("active", rightClickArmed);
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

            // Convert armed tap on canvas into a desktop right-click (button 2)
            window.addEventListener("pointerdown", function(e) {
                if (!rightClickArmed) return;
                if (bar.contains(e.target)) return;
                rightClickArmed = false;
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
        });
    })();
    """#
}
