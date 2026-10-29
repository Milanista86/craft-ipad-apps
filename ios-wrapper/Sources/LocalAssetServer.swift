import Foundation
import Network

/// A lightweight, 100% offline localhost HTTP server built on Apple's native Network.framework.
/// Serves the bundled WebAssembly + JS + HTML files on http://127.0.0.1:<port> so WKWebView
/// runs inside a Secure Context with full WebAssembly streaming, WebGL2/WebGPU, and IndexedDB support.
final class LocalAssetServer {
    private var listener: NWListener?
    private let rootDirectory: URL
    private let queue = DispatchQueue(label: "com.craftsuite.localserver", qos: .userInteractive, attributes: .concurrent)
    private(set) var port: UInt16 = 0

    init(rootDirectory: URL) {
        self.rootDirectory = rootDirectory
    }

    func start(preferredPort: UInt16, completion: @escaping (Result<UInt16, Error>) -> Void) {
        do {
            let params = NWParameters.tcp
            params.allowLocalEndpointReuse = true
            params.requiredLocalEndpoint = NWEndpoint.hostPort(
                host: NWEndpoint.Host("127.0.0.1"),
                port: NWEndpoint.Port(rawValue: preferredPort) ?? .any
            )

            let nwListener = try NWListener(using: params)
            self.listener = nwListener

            var didComplete = false
            nwListener.stateUpdateHandler = { [weak self] state in
                switch state {
                case .ready:
                    if !didComplete, let actualPort = nwListener.port?.rawValue {
                        didComplete = true
                        self?.port = actualPort
                        DispatchQueue.main.async {
                            completion(.success(actualPort))
                        }
                    }
                case .failed(let error):
                    if !didComplete {
                        didComplete = true
                        self?.listener?.cancel()
                        // Fallback to any available ephemeral port if preferredPort is busy
                        if preferredPort != 0 {
                            self?.start(preferredPort: 0, completion: completion)
                        } else {
                            DispatchQueue.main.async {
                                completion(.failure(error))
                            }
                        }
                    }
                default:
                    break
                }
            }

            nwListener.newConnectionHandler = { [weak self] connection in
                self?.handleConnection(connection)
            }

            nwListener.start(queue: queue)
        } catch {
            if preferredPort != 0 {
                start(preferredPort: 0, completion: completion)
            } else {
                completion(.failure(error))
            }
        }
    }

    func stop() {
        listener?.cancel()
        listener = nil
    }

    private func handleConnection(_ connection: NWConnection) {
        connection.start(queue: queue)
        connection.receive(minimumIncompleteLength: 1, maximumLength: 65536) { [weak self] data, _, isComplete, error in
            guard let self = self, error == nil, let data = data, !data.isEmpty else {
                connection.cancel()
                return
            }

            let requestString = String(decoding: data, as: UTF8.self)
            let firstLine = requestString.components(separatedBy: "\r\n").first ?? ""
            let parts = firstLine.components(separatedBy: " ")
            guard parts.count >= 2 else {
                connection.cancel()
                return
            }

            let method = parts[0].uppercased()
            var rawPath = parts[1]
            if let queryIndex = rawPath.firstIndex(of: "?") {
                rawPath = String(rawPath[..<queryIndex])
            }
            let decodedPath = rawPath.removingPercentEncoding ?? rawPath
            let relativePath = (decodedPath == "/" || decodedPath.isEmpty) ? "index.html" : String(decodedPath.dropFirst())

            var fileURL = self.rootDirectory.appendingPathComponent(relativePath).standardizedFileURL
            // Prevent directory traversal outside rootDirectory
            guard fileURL.path.hasPrefix(self.rootDirectory.standardizedFileURL.path) else {
                self.sendResponse(connection: connection, status: "403 Forbidden", mimeType: "text/plain", body: Data("Forbidden".utf8), headOnly: method == "HEAD")
                return
            }

            if !FileManager.default.fileExists(atPath: fileURL.path) {
                let fallbackURL = self.rootDirectory.appendingPathComponent((relativePath as NSString).lastPathComponent).standardizedFileURL
                if FileManager.default.fileExists(atPath: fallbackURL.path) {
                    fileURL = fallbackURL
                }
            }

            if FileManager.default.fileExists(atPath: fileURL.path),
               let fileData = try? Data(contentsOf: fileURL, options: .mappedIfSafe) {
                let mime = Self.mimeType(for: fileURL.pathExtension)
                self.sendResponse(connection: connection, status: "200 OK", mimeType: mime, body: fileData, headOnly: method == "HEAD")
            } else {
                self.sendResponse(connection: connection, status: "404 Not Found", mimeType: "text/plain", body: Data("Not Found".utf8), headOnly: method == "HEAD")
            }
        }
    }

    private func sendResponse(connection: NWConnection, status: String, mimeType: String, body: Data, headOnly: Bool) {
        let headers = [
            "HTTP/1.1 \(status)",
            "Content-Type: \(mimeType)",
            "Content-Length: \(body.count)",
            "Access-Control-Allow-Origin: *",
            "Cache-Control: no-cache",
            "Connection: close",
            "",
            ""
        ].joined(separator: "\r\n")

        var payload = Data(headers.utf8)
        if !headOnly {
            payload.append(body)
        }

        connection.send(
            content: payload,
            contentContext: .finalMessage,
            isComplete: true,
            completion: .contentProcessed { _ in }
        )
    }

    private static func mimeType(for ext: String) -> String {
        switch ext.lowercased() {
        case "html", "htm": return "text/html; charset=utf-8"
        case "js", "mjs": return "text/javascript; charset=utf-8"
        case "wasm": return "application/wasm"
        case "css": return "text/css; charset=utf-8"
        case "json", "map": return "application/json; charset=utf-8"
        case "svg": return "image/svg+xml"
        case "png": return "image/png"
        case "jpg", "jpeg": return "image/jpeg"
        case "webp": return "image/webp"
        case "ico": return "image/x-icon"
        case "ttf": return "font/ttf"
        case "otf": return "font/otf"
        case "woff": return "font/woff"
        case "woff2": return "font/woff2"
        default: return "application/octet-stream"
        }
    }
}
