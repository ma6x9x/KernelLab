import SwiftUI

struct ConsoleScreen: View {
    @ObservedObject var session: LabSession

    private let columns = [GridItem(.adaptive(minimum: 148), spacing: AppTheme.gap)]

    var body: some View {
        ZStack {
            ConsoleBackdrop()
            ScrollView {
                VStack(alignment: .leading, spacing: AppTheme.gap) {
                    Text("KernelLab")
                        .font(.title)
                        .bold()
                        .foregroundStyle(AppTheme.tint)
                    Text("App shell over the lab harness. APPLE-SUBMIT stays closed.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    TrainChipRow(session: session)
                    LazyVGrid(columns: columns, spacing: AppTheme.gap) {
                        ForEach(LabAction.allCases) { action in
                            StageButton(
                                title: action.title,
                                systemImage: action.systemImage,
                                disabled: session.busy,
                                action: { session.run(action) }
                            )
                        }
                    }
                    ReceiptPanel(session: session)
                    Text(session.status)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .accessibilityLabel("Status \(session.status)")
                    LogConsole(text: session.transcript)
                }
                .padding(AppTheme.pad)
            }
        }
    }
}
