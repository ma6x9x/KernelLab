import SwiftUI

struct ProbeFileRow: View {
    var file: ProbeFile
    var selected: Bool
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(file.name)
                        .font(.body)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    HStack(spacing: 4) {
                        Text(file.byteCount, format: .number)
                        Text("bytes")
                    }
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                }
                if selected {
                    Image(systemName: "checkmark")
                        .accessibilityHidden(true)
                }
            }
            .frame(minHeight: AppTheme.tap)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(file.name)
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}
