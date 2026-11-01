import Foundation

enum ReceiptExporter {
    static let defaultDirectory = "/var/jb/var/kernellab/receipts"
    static let defaultIPSDirectory = "/var/mobile/Library/Logs/CrashReporter"
    static let maxIPSFiles = 32
    static let maxIPSBytes = 8_000_000

    static func write(
        console: String,
        ident: LabRunResult,
        train: String,
        ipsDirectory: String,
        receiptDirectory: String
    ) -> ReceiptWrite {
        let folder = URL(fileURLWithPath: receiptDirectory, isDirectory: true)
        do {
            try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        } catch {
            return ReceiptWrite(
                message: "Could not create the receipt folder: \(error.localizedDescription)",
                path: nil
            )
        }

        let stamp = fileStamp(Date())
        let fileURL = folder.appendingPathComponent("kernellab-receipt-\(stamp).txt")
        let ipsFolder = folder.appendingPathComponent("ips-\(stamp)", isDirectory: true)
        let ipsReport = copyIPS(from: ipsDirectory, to: ipsFolder)

        var lines: [String] = []
        lines.append("KernelLab receipt")
        lines.append("train: \(train)")
        lines.append("cli: \(ident.executable.isEmpty ? "(missing)" : ident.executable)")
        lines.append("ident-status: \(ident.status)")
        lines.append("note: app shell transcript. APPLE-SUBMIT stays closed. This file is not an Apple submission.")
        lines.append("")
        lines.append("--- sim ident ---")
        lines.append(ident.output)
        lines.append("")
        lines.append("--- console ---")
        lines.append(console)
        lines.append("")
        lines.append("--- ips ---")
        lines.append(ipsReport)
        lines.append("")
        let body = lines.joined(separator: "\n")
        do {
            try Data(body.utf8).write(to: fileURL, options: .atomic)
        } catch {
            return ReceiptWrite(
                message: "Could not write the receipt: \(error.localizedDescription)",
                path: nil
            )
        }
        return ReceiptWrite(
            message: "Wrote \(fileURL.path)\n\(ipsReport)",
            path: fileURL.path
        )
    }

    private static func copyIPS(from sourcePath: String, to destination: URL) -> String {
        let trimmed = sourcePath.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            return "ips folder was empty. Set a path if you want .ips files copied."
        }
        var isDirectory: ObjCBool = false
        guard FileManager.default.fileExists(atPath: trimmed, isDirectory: &isDirectory), isDirectory.boolValue else {
            return "ips folder is not on disk: \(trimmed)"
        }
        let source = URL(fileURLWithPath: trimmed, isDirectory: true)
        guard let names = try? FileManager.default.contentsOfDirectory(atPath: trimmed) else {
            return "Could not list \(trimmed)"
        }
        let ipsNames = names.filter { $0.lowercased().hasSuffix(".ips") }.sorted()
        if ipsNames.isEmpty {
            return "No .ips files in \(trimmed)"
        }
        do {
            try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: true)
        } catch {
            return "Could not create \(destination.path): \(error.localizedDescription)"
        }
        var notes: [String] = []
        var copied = 0
        for name in ipsNames {
            if copied >= maxIPSFiles {
                notes.append("stopped after \(maxIPSFiles) files")
                break
            }
            let from = source.appendingPathComponent(name)
            let values = try? from.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey, .isSymbolicLinkKey])
            if values?.isSymbolicLink == true {
                notes.append("skipped symlink \(name)")
                continue
            }
            guard values?.isRegularFile == true else { continue }
            let bytes = values?.fileSize ?? 0
            if bytes > maxIPSBytes {
                notes.append("skipped \(name) (over \(maxIPSBytes) bytes)")
                continue
            }
            let to = destination.appendingPathComponent(name)
            do {
                if FileManager.default.fileExists(atPath: to.path) {
                    try FileManager.default.removeItem(at: to)
                }
                try FileManager.default.copyItem(at: from, to: to)
                notes.append("copied \(name) (\(bytes) bytes)")
                copied += 1
            } catch {
                notes.append("could not copy \(name): \(error.localizedDescription)")
            }
        }
        return notes.joined(separator: "\n")
    }

    private static func fileStamp(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "UTC")
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        return formatter.string(from: date)
    }
}
