import Foundation

enum LabAction: String, CaseIterable, Identifiable {
    case diff
    case simIdent
    case gate
    case listCaches
    case tables

    var id: String { rawValue }

    var title: String {
        switch self {
        case .diff:
            return "Diff"
        case .simIdent:
            return "Sim ident"
        case .gate:
            return "Show gate"
        case .listCaches:
            return "List caches"
        case .tables:
            return "Tables"
        }
    }

    var systemImage: String {
        switch self {
        case .diff:
            return "arrow.left.arrow.right"
        case .simIdent:
            return "checkmark.seal"
        case .gate:
            return "lock"
        case .listCaches:
            return "internaldrive"
        case .tables:
            return "tablecells"
        }
    }

    var arguments: [String] {
        switch self {
        case .diff:
            return ["diff"]
        case .simIdent:
            return ["sim", "ident"]
        case .gate:
            return ["gate"]
        case .listCaches:
            return ["target", "list"]
        case .tables:
            return ["tables"]
        }
    }
}
