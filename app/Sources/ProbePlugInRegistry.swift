import Foundation

enum ProbePlugInRegistry {
    static let plugs: [any ProbeWorkspacePlugIn] = []

    /// future: operator-supplied runner / codegen plugs here — authored by Kolby, not shipped.
    static let notice = "future: operator-supplied runner / codegen plugs here — authored by Kolby, not shipped."

    static func attachOperatorPlugIns() {
    }
}
