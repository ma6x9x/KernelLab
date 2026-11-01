import SwiftUI

struct PasteSlot: View {
    var title: String
    var fileExtension: String
    @Binding var draft: String
    @Binding var name: String
    var onSave: () -> Void
    var onStub: () -> Void

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: AppTheme.gap) {
                Text(title)
                    .font(.headline)
                Text("Kolby pastes. Empty until you type. Saving writes that text into the workspace and nothing else.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                ZStack(alignment: .topLeading) {
                    if draft.isEmpty {
                        Text("Kolby pastes")
                            .foregroundStyle(.secondary)
                            .padding(.top, 8)
                            .padding(.leading, 4)
                            .allowsHitTesting(false)
                            .accessibilityHidden(true)
                    }
                    TextEditor(text: $draft)
                        .font(.system(.body, design: .monospaced))
                        .frame(minHeight: 120)
                        .pathTyping()
                        .accessibilityLabel("\(title) paste slot")
                }
                TextField("File name", text: $name)
                    .pathTyping()
                    .textFieldStyle(.roundedBorder)
                    .accessibilityLabel("\(fileExtension) file name")
                Button("Save .\(fileExtension)", action: onSave)
                    .frame(minHeight: AppTheme.tap)
                Button("Create empty .\(fileExtension) stub", action: onStub)
                    .frame(minHeight: AppTheme.tap)
            }
        }
    }
}
