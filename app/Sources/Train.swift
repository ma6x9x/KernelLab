import Foundation

enum Train: String, CaseIterable, Identifiable, Equatable {
    case twentySixFive = "26.5"
    case twentySeven = "27.0"

    var id: String { rawValue }

    var baseline: Train {
        switch self {
        case .twentySixFive:
            return .twentySeven
        case .twentySeven:
            return .twentySixFive
        }
    }

    var chipDetail: String {
        switch self {
        case .twentySixFive:
            return "Host, baseline 27.0"
        case .twentySeven:
            return "Host, baseline 26.5"
        }
    }

    var setArguments: [String] {
        ["target", "set", "--train", rawValue, "--baseline-train", baseline.rawValue]
    }
}
