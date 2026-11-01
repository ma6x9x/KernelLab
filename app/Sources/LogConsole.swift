import SwiftUI

struct LogConsole: View {
    var text: String

    var body: some View {
        GlassPanel {
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        Text(text.isEmpty ? " " : text)
                            .font(.system(.body, design: .monospaced))
                            .foregroundStyle(.primary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                        Color.clear
                            .frame(height: 1)
                            .id("log-end")
                            .accessibilityHidden(true)
                    }
                }
                .frame(minHeight: 280)
                .onChange(of: text) { _ in
                    proxy.scrollTo("log-end", anchor: .bottom)
                }
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Lab output")
    }
}
