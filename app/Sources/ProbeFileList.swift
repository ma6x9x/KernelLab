import SwiftUI

struct ProbeFileList: View {
    @ObservedObject var workspace: ProbeWorkspace

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: AppTheme.gap) {
                Text("Sources")
                    .font(.headline)
                if workspace.files.isEmpty {
                    Text("No .m or .h files yet.")
                        .font(.body)
                        .foregroundStyle(.secondary)
                        .frame(minHeight: AppTheme.tap, alignment: .leading)
                } else {
                    ForEach(workspace.files) { file in
                        ProbeFileRow(
                            file: file,
                            selected: workspace.selectedPath == file.path,
                            action: { workspace.load(file) }
                        )
                    }
                }
            }
        }
    }
}
