import SwiftUI

struct ProbePathBar: View {
    @ObservedObject var workspace: ProbeWorkspace

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: AppTheme.gap) {
                Text("Workspace")
                    .font(.headline)
                TextField("Probes folder", text: $workspace.rootPath)
                    .pathTyping()
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { workspace.refresh() }
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 148), spacing: AppTheme.gap)], spacing: AppTheme.gap) {
                    StageButton(title: "Refresh", systemImage: "arrow.clockwise", disabled: false) { workspace.refresh() }
                    StageButton(title: "Default folder", systemImage: "externaldrive", disabled: false) { workspace.useDefaultFolder() }
                    StageButton(title: "Documents", systemImage: "folder", disabled: false) { workspace.useDocumentsFolder() }
                    StageButton(title: "Create folder", systemImage: "folder.badge.plus", disabled: false) { workspace.createFolder() }
                }
            }
        }
    }
}
