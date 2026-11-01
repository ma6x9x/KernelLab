import Combine
import Foundation

@MainActor
final class ProbeWorkspace: ObservableObject {
    static let defaultRoot = "/var/jb/var/kernellab/probes"
    static let storageKey = "kernellab.probesRoot"

    @Published var rootPath: String
    @Published var files: [ProbeFile] = []
    @Published var message = "User-owned sources only."
    @Published var preview = ""
    @Published var selectedPath: String?
    @Published var implementationDraft = ""
    @Published var headerDraft = ""
    @Published var implementationName = ""
    @Published var headerName = ""

    private var refreshGeneration = 0

    init() {
        rootPath = UserDefaults.standard.string(forKey: Self.storageKey) ?? Self.defaultRoot
    }

    static var documentsPath: String {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first?.path
            ?? (NSHomeDirectory() + "/Documents")
    }

    func useDefaultFolder() {
        rootPath = Self.defaultRoot
        refresh()
    }

    func useDocumentsFolder() {
        rootPath = Self.documentsPath
        refresh()
    }

    func createFolder() {
        let path = trimmedRoot()
        rootPath = path
        do {
            try FileManager.default.createDirectory(atPath: path, withIntermediateDirectories: true)
            message = "Created \(path)"
            refresh()
        } catch {
            message = "Could not create folder: \(error.localizedDescription)"
        }
    }

    func refresh() {
        let path = trimmedRoot()
        rootPath = path
        UserDefaults.standard.set(path, forKey: Self.storageKey)
        ProbePlugInRegistry.attachOperatorPlugIns()
        refreshGeneration += 1
        let generation = refreshGeneration
        let selected = selectedPath
        message = "Reading the folder."
        Task.detached {
            let scan = ProbeScanner.scan(rootPath: path)
            let kept: String?
            if let selected, scan.files.contains(where: { $0.path == selected }) {
                kept = ProbeScanner.preview(path: selected, rootPath: path)
            } else {
                kept = nil
            }
            await MainActor.run {
                guard generation == self.refreshGeneration else { return }
                self.files = scan.files
                self.message = scan.message
                if let kept {
                    self.preview = kept
                } else {
                    self.selectedPath = nil
                    self.preview = ""
                }
            }
        }
    }

    func load(_ file: ProbeFile) {
        selectedPath = file.path
        preview = ProbeScanner.preview(path: file.path, rootPath: rootPath)
    }

    func saveImplementation() {
        save(draft: implementationDraft, stem: implementationName, fileExtension: "m")
    }

    func saveHeader() {
        save(draft: headerDraft, stem: headerName, fileExtension: "h")
    }

    func createImplementationStub() {
        write(text: ProbeNames.stubText, stem: implementationName.isEmpty ? "kolby" : implementationName, fileExtension: "m")
    }

    func createHeaderStub() {
        write(text: ProbeNames.stubText, stem: headerName.isEmpty ? "kolby" : headerName, fileExtension: "h")
    }

    private func save(draft: String, stem: String, fileExtension: String) {
        if draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            message = "Paste slot is empty. Kolby pastes."
            return
        }
        write(text: draft, stem: stem, fileExtension: fileExtension)
    }

    private func write(text: String, stem: String, fileExtension: String) {
        let path = trimmedRoot()
        rootPath = path
        guard let fileName = ProbeNames.sourceFileName(stem: stem, fileExtension: fileExtension) else {
            message = "Use a file name of letters, numbers, dash, or underscore."
            return
        }
        let root = URL(fileURLWithPath: path, isDirectory: true)
        do {
            try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        } catch {
            message = "Could not create the probes folder: \(error.localizedDescription)"
            return
        }
        let resolvedRoot = root.resolvingSymlinksInPath()
        let destination = resolvedRoot.appendingPathComponent(fileName)
        guard ProbeScanner.contains(destination.deletingLastPathComponent(), root: resolvedRoot) else {
            message = "Refusing to write outside the probes folder."
            return
        }
        if FileManager.default.fileExists(atPath: destination.path) {
            let values = try? destination.resourceValues(forKeys: [.isSymbolicLinkKey])
            if values?.isSymbolicLink == true {
                message = "Refusing to follow a symlink."
                return
            }
            message = "\(fileName) already exists. Pick another name or remove it in Filza."
            return
        }
        do {
            try Data(text.utf8).write(to: destination, options: .atomic)
            message = "Saved \(fileName). KernelLab does not compile or run it."
            refresh()
        } catch {
            message = "Could not save \(fileName): \(error.localizedDescription)"
        }
    }

    private func trimmedRoot() -> String {
        let trimmed = rootPath.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? Self.defaultRoot : trimmed
    }
}
