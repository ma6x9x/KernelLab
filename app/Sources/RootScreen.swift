import SwiftUI

struct RootScreen: View {
    @StateObject private var session = LabSession()
    @StateObject private var probes = ProbeWorkspace()

    var body: some View {
        TabView {
            ConsoleScreen(session: session)
                .tabItem {
                    Label("Console", systemImage: "terminal")
                }
            ProbesScreen(workspace: probes)
                .tabItem {
                    Label("Probes", systemImage: "folder")
                }
        }
        .tint(AppTheme.tint)
        .preferredColorScheme(.dark)
    }
}
