import SwiftUI

struct PathTyping: ViewModifier {
    @ViewBuilder
    func body(content: Content) -> some View {
        if #available(iOS 16, *) {
            content
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled(true)
        } else {
            content
                .textInputAutocapitalization(.never)
                .disableAutocorrection(true)
        }
    }
}

extension View {
    func pathTyping() -> some View {
        modifier(PathTyping())
    }
}
