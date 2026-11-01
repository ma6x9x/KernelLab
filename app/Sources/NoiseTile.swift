import SwiftUI

enum NoiseTile {
    static let image: UIImage = {
        let size = CGSize(width: 96, height: 96)
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        return UIGraphicsImageRenderer(size: size, format: format).image { context in
            var generator = SystemRandomNumberGenerator()
            for y in 0..<Int(size.height) {
                for x in 0..<Int(size.width) {
                    let value = CGFloat(UInt8.random(in: 0...255, using: &generator)) / 255
                    UIColor(white: value, alpha: 1).setFill()
                    context.fill(CGRect(x: x, y: y, width: 1, height: 1))
                }
            }
        }
    }()
}
