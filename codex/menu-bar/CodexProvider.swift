import AppKit
import Foundation

private struct HelperConfiguration: Decodable {
    let python: String
    let script: String
    let root: String
}

private struct ProviderState: Decodable {
    let selected: String
    let config_in_sync: Bool
    let state_file: String?
    let config_file: String?
}

private struct HelperError: Decodable, Error {
    let message: String
    let hint: String?
}

private struct HelperEnvelope: Decodable {
    let data: ProviderState?
    let error: HelperError?
}

private enum HelperResult {
    case success(ProviderState)
    case failure(String)
}

// The helper is the only writer of provider state. AppKit work stays on the
// main thread; the subprocess and decoding run on a serial background queue.
private final class ProviderMenu: NSObject, NSApplicationDelegate, NSMenuDelegate {
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
    private let menu = NSMenu()
    private let worker = DispatchQueue(label: "io.adithyan.codex-provider.helper", qos: .userInitiated)
    private var subscriptionItem: NSMenuItem!
    private var azureItem: NSMenuItem!
    private var noticeItem: NSMenuItem!
    private var state: ProviderState?
    private var busy = false
    private var lastError: String?
    private var watchedFiles: [String] = []
    private var fileStamps: [String] = []
    private var refreshTimer: Timer?
    private let inspect = CommandLine.arguments.contains("--inspect-menu")
    private var showOnLaunch = CommandLine.arguments.contains("--show-menu")

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Finder launches should reuse the login instance rather than add a
        // second menu item. Inspection is a separate short-lived read operation.
        if !inspect, let identifier = Bundle.main.bundleIdentifier,
           NSRunningApplication.runningApplications(withBundleIdentifier: identifier)
            .contains(where: { $0.processIdentifier != ProcessInfo.processInfo.processIdentifier }) {
            NSApp.terminate(nil)
            return
        }

        NSApp.setActivationPolicy(.accessory)
        menu.autoenablesItems = false
        menu.delegate = self
        let heading = NSMenuItem(title: "Provider on this Mac", action: nil, keyEquivalent: "")
        heading.isEnabled = false
        menu.addItem(heading)
        subscriptionItem = choice("Codex subscription", provider: "subscription")
        azureItem = choice("Azure credits", provider: "azure")
        menu.addItem(subscriptionItem)
        menu.addItem(azureItem)
        menu.addItem(.separator())
        noticeItem = NSMenuItem(title: "Reading provider…", action: #selector(showError), keyEquivalent: "")
        noticeItem.target = self
        noticeItem.isEnabled = false
        menu.addItem(noticeItem)
        for text in ["Desktop app + default terminal sessions", "Reopen Codex and start a new task."] {
            let item = NSMenuItem(title: text, action: nil, keyEquivalent: "")
            item.isEnabled = false
            menu.addItem(item)
        }
        menu.addItem(.separator())
        let quit = NSMenuItem(title: "Quit Codex Provider", action: #selector(quitApp), keyEquivalent: "q")
        quit.target = self
        menu.addItem(quit)
        statusItem.menu = menu
        let icon = NSImage(systemSymbolName: "arrow.triangle.2.circlepath", accessibilityDescription: "Codex provider")?
            .withSymbolConfiguration(NSImage.SymbolConfiguration(pointSize: 16, weight: .medium))
        icon?.isTemplate = true
        statusItem.button?.image = icon
        statusItem.button?.imagePosition = .imageOnly
        statusItem.button?.setAccessibilityLabel("Codex provider")
        render()
        run("status")
        // Two inexpensive stat calls detect CLI/sync changes. The helper only
        // runs when these files change, or when the user opens the menu.
        let timer = Timer(timeInterval: 2, repeats: true) { [weak self] _ in
            guard let self = self, !self.busy, !self.watchedFiles.isEmpty else { return }
            let stamps = self.currentFileStamps()
            if stamps != self.fileStamps {
                self.fileStamps = stamps
                self.run("status")
            }
        }
        RunLoop.main.add(timer, forMode: .common)
        refreshTimer = timer
    }

    private func choice(_ title: String, provider: String) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: #selector(selectProvider(_:)), keyEquivalent: "")
        item.target = self
        item.representedObject = provider
        return item
    }

    func menuWillOpen(_ menu: NSMenu) {
        run("status")
    }

    @objc private func selectProvider(_ sender: NSMenuItem) {
        guard let selected = sender.representedObject as? String else { return }
        // Reapplying the current selection also repairs a config changed outside
        // the menu, using the same transactional helper as terminal callers.
        run(selected)
    }

    private func render() {
        statusItem.button?.title = ""
        let fullName = state?.selected == "azure" ? "Azure credits" : "Codex subscription"
        statusItem.button?.toolTip = state == nil ? "Choose the Codex provider for this Mac" : "\(fullName) on this Mac"
        statusItem.button?.setAccessibilityValue(state == nil ? "Loading" : fullName)
        subscriptionItem?.state = state?.selected == "subscription" ? .on : .off
        azureItem?.state = state?.selected == "azure" ? .on : .off
        subscriptionItem?.isEnabled = !busy
        azureItem?.isEnabled = !busy
        noticeItem?.isEnabled = !busy && lastError != nil
        if busy {
            noticeItem?.title = state == nil ? "Reading provider…" : "Updating…"
        } else if lastError != nil {
            noticeItem?.title = "Provider error…"
            statusItem.button?.toolTip = "Unable to update the provider. Open the menu for details."
        } else if state?.config_in_sync == false {
            noticeItem?.title = "Select a provider to apply it."
        } else {
            noticeItem?.title = "Applies to this Mac only"
        }
    }

    private func run(_ command: String) {
        guard !busy else { return }
        busy = true
        render()
        worker.async {
            let result = Self.invokeHelper(command)
            DispatchQueue.main.async {
                self.busy = false
                switch result {
                case .success(let newState):
                    self.state = newState
                    self.lastError = nil
                    self.watchedFiles = [newState.state_file, newState.config_file].compactMap { $0 }
                    self.fileStamps = self.currentFileStamps()
                case .failure(let message):
                    self.lastError = message
                }
                self.render()
                if self.inspect {
                    self.printInspection()
                    exit(self.lastError == nil ? 0 : 1)
                }
                if command != "status", self.lastError != nil {
                    self.showError()
                } else if self.showOnLaunch && command == "status" {
                    // Only the first launch refresh opens the menu. Later
                    // menuWillOpen refreshes must not recursively reopen it.
                    self.showOnLaunch = false
                    self.perform(#selector(self.showMenu), with: nil, afterDelay: 0.1)
                }
            }
        }
    }

    private func currentFileStamps() -> [String] {
        watchedFiles.map { path in
            guard let attributes = try? FileManager.default.attributesOfItem(atPath: path) else { return "missing" }
            let modified = (attributes[.modificationDate] as? Date)?.timeIntervalSince1970 ?? 0
            return "\(modified):\(attributes[.size] ?? ""):\(attributes[.systemFileNumber] ?? "")"
        }
    }

    @objc private func showMenu() {
        guard let button = statusItem.button else { return }
        menu.popUp(positioning: nil, at: NSPoint(x: 0, y: button.bounds.minY), in: button)
    }

    private static func invokeHelper(_ command: String) -> HelperResult {
        do {
            guard let url = Bundle.main.url(forResource: "provider-menu", withExtension: "json") else {
                return .failure("The app configuration is missing. Reinstall Codex Provider from the agents repository.")
            }
            let config = try JSONDecoder().decode(HelperConfiguration.self, from: Data(contentsOf: url))
            let process = Process()
            process.executableURL = URL(fileURLWithPath: config.python)
            process.arguments = [config.script, command, "--no-input"] + (command == "status" ? [] : ["--apply"])
            process.currentDirectoryURL = URL(fileURLWithPath: config.root)
            var environment = ProcessInfo.processInfo.environment
            environment["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
            environment["PYTHONUNBUFFERED"] = "1"
            process.environment = environment
            let output = Pipe()
            process.standardOutput = output
            // The helper's JSON error is the public diagnostic; do not surface
            // arbitrary subprocess stderr in the native interface.
            process.standardError = FileHandle.nullDevice
            try process.run()
            let timeout = DispatchWorkItem {
                if process.isRunning { process.terminate() }
            }
            DispatchQueue.global().asyncAfter(deadline: .now() + 180, execute: timeout)
            let bytes = output.fileHandleForReading.readDataToEndOfFile()
            process.waitUntilExit()
            timeout.cancel()
            guard let envelope = try? JSONDecoder().decode(HelperEnvelope.self, from: bytes) else {
                return .failure("The provider helper did not return a valid result. Try again or run scripts/codex-provider.py status in the agents repository.")
            }
            if let error = envelope.error {
                return .failure([error.message, error.hint].compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: "\n\n"))
            }
            guard process.terminationStatus == 0,
                  let data = envelope.data,
                  ["azure", "subscription"].contains(data.selected) else {
                return .failure("The provider could not be read or applied. Try again from the menu.")
            }
            if command != "status", !data.config_in_sync {
                return .failure("The selection was not fully applied. Run scripts/codex-provider.py status in the agents repository for details.")
            }
            return .success(data)
        } catch {
            return .failure("The provider helper could not run. Reinstall Codex Provider or check that the agents repository and Python are available.\n\n\(error.localizedDescription)")
        }
    }

    private func printInspection() {
        let result: [String: Any] = [
            "title": statusItem.button?.title ?? "",
            "has_icon": statusItem.button?.image != nil,
            "tooltip": statusItem.button?.toolTip ?? "",
            "selected": state?.selected as Any? ?? NSNull(),
            "config_in_sync": state?.config_in_sync as Any? ?? NSNull(),
            "error": lastError as Any? ?? NSNull(),
            "items": menu.items.filter { !$0.isSeparatorItem }.map { item in
                ["title": item.title, "enabled": item.isEnabled, "checked": item.state == .on] as [String: Any]
            },
        ]
        if let bytes = try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]),
           let text = String(data: bytes, encoding: .utf8) {
            print(text)
        }
    }

    @objc private func showError() {
        guard let message = lastError else { return }
        let alert = NSAlert()
        alert.messageText = "Codex provider could not be updated"
        alert.informativeText = message
        alert.alertStyle = .warning
        alert.addButton(withTitle: "OK")
        NSApp.activate(ignoringOtherApps: true)
        alert.runModal()
    }

    @objc private func quitApp() {
        NSApp.terminate(nil)
    }
}

let application = NSApplication.shared
private let delegate = ProviderMenu()
application.delegate = delegate
application.run()
