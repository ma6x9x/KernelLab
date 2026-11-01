import Foundation

enum ProbeScanner {
    static let maxFiles = 500
    static let maxDepth = 8

    static func scan(rootPath: String) -> ProbeScan {
        let root = URL(fileURLWithPath: rootPath, isDirectory: true)
        let accessing = root.startAccessingSecurityScopedResource()
        defer {
            if accessing {
                root.stopAccessingSecurityScopedResource()
            }
        }
        var isDirectory: ObjCBool = false
        let exists = FileManager.default.fileExists(atPath: root.path, isDirectory: &isDirectory)
        if !exists {
            return ProbeScan(
                files: [],
                message: "Folder is not on disk yet. Create it, or drop files with Filza, then Refresh."
            )
        }
        if !isDirectory.boolValue {
            return ProbeScan(files: [], message: "That path is a file. Choose a folder.")
        }
        let resolvedRoot = root.resolvingSymlinksInPath()
        guard let enumerator = FileManager.default.enumerator(
            at: resolvedRoot,
            includingPropertiesForKeys: [.isRegularFileKey, .fileSizeKey, .isSymbolicLinkKey],
            options: [.skipsHiddenFiles]
        ) else {
            return ProbeScan(files: [], message: "Could not read \(resolvedRoot.path)")
        }

        var files: [ProbeFile] = []
        var truncated = false
        for case let url as URL in enumerator {
            let depth = url.pathComponents.count - resolvedRoot.pathComponents.count
            if depth > maxDepth {
                enumerator.skipDescendants()
                continue
            }
            guard isSource(url) else { continue }
            let resolved = url.resolvingSymlinksInPath()
            guard contains(resolved, root: resolvedRoot) else { continue }
            let values = try? url.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey, .isSymbolicLinkKey])
            if values?.isSymbolicLink == true {
                continue
            }
            guard values?.isRegularFile == true else { continue }
            files.append(
                ProbeFile(
                    path: url.path,
                    name: relativeName(of: url, root: resolvedRoot),
                    byteCount: values?.fileSize ?? 0
                )
            )
            if files.count >= maxFiles {
                truncated = true
                break
            }
        }
        files.sort { $0.name.localizedStandardCompare($1.name) == .orderedAscending }
        var message = files.isEmpty
            ? "No .m or .h files in this folder. User-owned sources only."
            : "\(files.count) source file(s). KernelLab does not compile or run them."
        if truncated {
            message += " Listing stopped at \(maxFiles) files."
        }
        return ProbeScan(files: files, message: message)
    }

    static func contains(_ url: URL, root: URL) -> Bool {
        let rootPath = root.standardizedFileURL.path
        let path = url.standardizedFileURL.path
        if path == rootPath {
            return true
        }
        let prefix = rootPath.hasSuffix("/") ? rootPath : rootPath + "/"
        return path.hasPrefix(prefix)
    }

    static func isSource(_ url: URL) -> Bool {
        let ext = url.pathExtension.lowercased()
        return ext == "m" || ext == "h"
    }

    private static func relativeName(of url: URL, root: URL) -> String {
        let rootPath = root.standardizedFileURL.path
        let path = url.standardizedFileURL.path
        let prefix = rootPath.hasSuffix("/") ? rootPath : rootPath + "/"
        if path.hasPrefix(prefix) {
            return String(path.dropFirst(prefix.count))
        }
        return url.lastPathComponent
    }
}
