import SwiftUI

struct StageButton: View {
    var title: String
    var systemImage: String
    var disabled: Bool
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            Label(title, systemImage: systemImage)
                .font(.body)
                .frame(maxWidth: .infinity, minHeight: AppTheme.tap)
        }
        .buttonStyle(StageGlassButtonStyle())
        .disabled(disabled)
        .accessibilityLabel(title)
    }
}
