import SwiftUI

struct StageGlassButtonStyle: ButtonStyle {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency
    @Environment(\.colorSchemeContrast) private var contrast

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundStyle(AppTheme.tint)
            .padding(.horizontal, 8)
            .background(fill)
            .overlay(rim)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .scaleEffect(configuration.isPressed && !reduceMotion ? 1.03 : 1)
            .animation(reduceMotion ? .none : .spring(), value: configuration.isPressed)
    }

    @ViewBuilder
    private var fill: some View {
        if reduceTransparency {
            RoundedRectangle(cornerRadius: 18).fill(Color(.secondarySystemBackground))
        } else {
            RoundedRectangle(cornerRadius: 18).fill(.ultraThinMaterial)
        }
    }

    private var rim: some View {
        let width: CGFloat = contrast == .increased ? 1.5 : 0.5
        return RoundedRectangle(cornerRadius: 18)
            .strokeBorder(Color.white.opacity(contrast == .increased ? 0.7 : 0.28), lineWidth: width)
            .allowsHitTesting(false)
    }
}
