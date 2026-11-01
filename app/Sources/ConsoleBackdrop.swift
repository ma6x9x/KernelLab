import SwiftUI

struct ConsoleBackdrop: View {
    var body: some View {
        LinearGradient(
            colors: [AppTheme.backgroundTop, AppTheme.backgroundBottom],
            startPoint: .top,
            endPoint: .bottom
        )
        .overlay(alignment: .topLeading) {
            Circle()
                .fill(AppTheme.wash.opacity(0.22))
                .frame(width: 280, height: 280)
                .blur(radius: 70)
                .offset(x: -60, y: -40)
                .accessibilityHidden(true)
        }
        .overlay(alignment: .bottomTrailing) {
            Circle()
                .fill(Color.purple.opacity(0.16))
                .frame(width: 320, height: 320)
                .blur(radius: 80)
                .offset(x: 40, y: 60)
                .accessibilityHidden(true)
        }
        .ignoresSafeArea()
    }
}
