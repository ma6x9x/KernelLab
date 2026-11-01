import Foundation

struct ProbeFile: Identifiable, Equatable, Hashable {
    var path: String
    var name: String
    var byteCount: Int

    var id: String { path }
}
