import SwiftUI

struct GlassPanel<Content: View>: View {
    var selected: Bool = false
    var cornerRadius: CGFloat = AppTheme.corner
    @ViewBuilder var content: () -> Content

    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency
    @Environment(\.colorSchemeContrast) private var contrast
    @Environment(\.colorScheme) private var scheme

    var body: some View {
        content()
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(background)
            .overlay(innerShadow)
            .overlay(rim)
            .overlay(grain)
            .clipShape(shape)
            .shadow(
                color: .black.opacity(scheme == .dark ? 0.35 : 0.12),
                radius: 16,
                x: 0,
                y: 8
            )
    }

    private var shape: RoundedRectangle {
        RoundedRectangle(cornerRadius: cornerRadius)
    }

    @ViewBuilder
    private var background: some View {
        if reduceTransparency {
            shape.fill(Color(.secondarySystemBackground))
        } else {
            ZStack {
                shape.fill(.ultraThinMaterial)
                shape.fill(AppTheme.wash.opacity(scheme == .dark ? 0.10 : 0.06))
                shape.fill(
                    LinearGradient(
                        colors: [.white.opacity(0.10), .clear],
                        startPoint: .top,
                        endPoint: .center
                    )
                )
            }
        }
    }

    private var innerShadow: some View {
        shape
            .stroke(Color.black.opacity(scheme == .dark ? 0.45 : 0.18), lineWidth: 6)
            .blur(radius: 6)
            .offset(y: 3)
            .mask(shape)
            .allowsHitTesting(false)
    }

    private var rim: some View {
        let boost = contrast == .increased || selected
        return ZStack {
            shape.strokeBorder(
                LinearGradient(
                    stops: [
                        .init(color: .white.opacity(boost ? 0.85 : 0.55), location: 0),
                        .init(color: .white.opacity(0.08), location: 0.42),
                        .init(color: .white.opacity(boost ? 0.28 : 0.14), location: 1),
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                ),
                lineWidth: boost ? 1.5 : 1
            )
            .blendMode(.plusLighter)
            shape.strokeBorder(
                Color.primary.opacity(boost ? 0.45 : 0.08),
                lineWidth: boost ? 1 : 0.5
            )
        }
        .allowsHitTesting(false)
    }

    private var grain: some View {
        Image(uiImage: NoiseTile.image)
            .resizable(resizingMode: .tile)
            .opacity(reduceTransparency ? 0 : 0.035)
            .blendMode(.overlay)
            .allowsHitTesting(false)
            .accessibilityHidden(true)
    }
}
