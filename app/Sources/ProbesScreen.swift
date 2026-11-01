import SwiftUI
import UniformTypeIdentifiers

struct ProbesScreen: View {
    @ObservedObject var workspace: ProbeWorkspace
    @State private var pickingFolder = false

    var body: some View {
        ZStack {
            ConsoleBackdrop()
            ScrollView {
                VStack(alignment: .leading, spacing: AppTheme.gap) {
                    Text("Probes")
                        .font(.title)
                        .bold()
                        .foregroundStyle(AppTheme.tint)
                    Text("User-owned sources only. Drop .m and .h files with Filza, then Refresh. New files show up without reinstalling the app.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Text(workspace.message)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    ProbePathBar(workspace: workspace)
                    Button("Choose folder", action: { pickingFolder = true })
                        .frame(minHeight: AppTheme.tap)
                    ProbeFileList(workspace: workspace)
                    ProbePreview(text: workspace.preview)
                    PasteSlot(
                        title: "Paste slot — implementation file",
                        fileExtension: "m",
                        draft: $workspace.implementationDraft,
                        name: $workspace.implementationName,
                        onSave: workspace.saveImplementation,
                        onStub: workspace.createImplementationStub
                    )
                    PasteSlot(
                        title: "Paste slot — header file",
                        fileExtension: "h",
                        draft: $workspace.headerDraft,
                        name: $workspace.headerName,
                        onSave: workspace.saveHeader,
                        onStub: workspace.createHeaderStub
                    )
                    GlassPanel {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Extension point")
                                .font(.headline)
                            Text(ProbePlugInRegistry.notice)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            Text("Shipped plug-ins: \(ProbePlugInRegistry.plugs.count). Nothing in this tab executes a source file.")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .padding(AppTheme.pad)
            }
        }
        .onAppear { workspace.refresh() }
        .fileImporter(
            isPresented: $pickingFolder,
            allowedContentTypes: [.folder],
            allowsMultipleSelection: false
        ) { result in
            applyFolderPick(result)
        }
    }

    private func applyFolderPick(_ result: Result<[URL], Error>) {
        switch result {
        case .failure(let error):
            workspace.message = error.localizedDescription
        case .success(let urls):
            guard let url = urls.first else {
                workspace.message = "No folder selected."
                return
            }
            let accessing = url.startAccessingSecurityScopedResource()
            workspace.rootPath = url.path
            if accessing {
                url.stopAccessingSecurityScopedResource()
            }
            workspace.refresh()
        }
    }
}
