import SwiftUI

struct TrainChipRow: View {
    @ObservedObject var session: LabSession
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize

    var body: some View {
        if dynamicTypeSize.isAccessibilitySize {
            VStack(spacing: AppTheme.gap) {
                TrainChipList(session: session)
            }
        } else {
            HStack(spacing: AppTheme.gap) {
                TrainChipList(session: session)
            }
        }
    }
}
