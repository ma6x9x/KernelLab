import Combine
import Foundation

@MainActor
final class LabSession: ObservableObject {
    @Published var train: Train
    @Published var transcript: String
    @Published var status: String
    @Published var busy = false

    init() {
        let storedTrain = UserDefaults.standard.string(forKey: "kernellab.train") ?? Train.twentySixFive.rawValue
        train = Train(rawValue: storedTrain) ?? .twentySixFive
        transcript = """
        KernelLab app shell
        Commands run the installed kernellab CLI.
        APPLE-SUBMIT stays closed.
        This app does not ship kernel caches.
        """
        status = "Ready"
    }

    func selectTrain(_ train: Train) {
        self.train = train
        UserDefaults.standard.set(train.rawValue, forKey: "kernellab.train")
        run(arguments: train.setArguments, title: "target set \(train.rawValue)")
    }

    func run(_ action: LabAction) {
        run(arguments: action.arguments, title: action.title)
    }

    private func run(arguments: [String], title: String) {
        guard !busy else { return }
        busy = true
        status = "Running \(title)"
        let shown = (["kernellab"] + arguments).joined(separator: " ")
        append("$ \(shown)")
        Task.detached {
            let result = LabRunner.run(arguments)
            let text = result.output
            let status = result.status
            await MainActor.run {
                self.finish(text: text, status: status, title: title)
            }
        }
    }

    private func finish(text: String, status: Int32, title: String) {
        append(text)
        append("exit \(status)")
        self.status = status == 0 ? "\(title) finished" : "\(title) exited \(status)"
        busy = false
    }

    private func append(_ text: String) {
        if transcript.isEmpty {
            transcript = text
        } else {
            transcript += "\n" + text
        }
    }
}
