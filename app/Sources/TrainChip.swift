import SwiftUI

struct TrainChip: View {
    var train: Train
    var selected: Bool
    var disabled: Bool
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            GlassPanel(selected: selected, cornerRadius: 18) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(train.rawValue)
                        .font(.headline)
                    Text(train.chipDetail)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, minHeight: AppTheme.tap, alignment: .leading)
            }
        }
        .buttonStyle(.plain)
        .disabled(disabled)
        .accessibilityLabel("\(train.rawValue). \(train.chipDetail)")
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}
