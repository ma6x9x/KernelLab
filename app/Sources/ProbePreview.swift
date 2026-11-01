import SwiftUI

struct ProbePreview: View {
    var text: String

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: AppTheme.gap) {
                Text("Preview")
                    .font(.headline)
                Text("Read only. KernelLab does not compile or run this file.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Text(text.isEmpty ? "Select a file." : text)
                    .font(.system(.body, design: .monospaced))
                    .frame(maxWidth: .infinity, minHeight: AppTheme.tap, alignment: .topLeading)
                    .textSelection(.enabled)
            }
        }
        .accessibilityLabel("Source preview")
    }
}
