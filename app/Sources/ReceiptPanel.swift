import SwiftUI

struct ReceiptPanel: View {
    @ObservedObject var session: LabSession

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: AppTheme.gap) {
                Text("Receipt")
                    .font(.headline)
                Text("Export runs sim ident, saves this console, and copies .ips files from the folder below.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                TextField("Receipt folder", text: $session.receiptPath)
                    .pathTyping()
                    .textFieldStyle(.roundedBorder)
                TextField("IPS folder", text: $session.ipsPath)
                    .pathTyping()
                    .textFieldStyle(.roundedBorder)
                Button("Export ident + console + ips") {
                    session.exportReceipt()
                }
                    .frame(minHeight: AppTheme.tap)
                    .disabled(session.busy)
            }
        }
    }
}
