import Foundation

enum ProbeNames {
    static let stubText = """
    // Kolby pastes
    // user-owned sources only
    // KernelLab does not compile or run this file.

    """

    static func sourceFileName(stem: String, fileExtension: String) -> String? {
        let cleaned = fileExtension.lowercased()
        guard cleaned == "m" || cleaned == "h" else { return nil }
        var name = stem.trimmingCharacters(in: .whitespacesAndNewlines)
        let suffix = "." + cleaned
        if name.lowercased().hasSuffix(suffix) {
            name = String(name.dropLast(suffix.count))
        }
        guard !name.isEmpty else { return nil }
        guard !name.contains("/"), !name.contains("\\"), !name.contains("..") else { return nil }
        guard name != ".", name != ".." else { return nil }
        let allowed = CharacterSet(charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        guard name.unicodeScalars.allSatisfy({ allowed.contains($0) }) else { return nil }
        return name + suffix
    }
}
