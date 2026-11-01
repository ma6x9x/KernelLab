import SwiftUI

struct TrainChipList: View {
    @ObservedObject var session: LabSession

    var body: some View {
        ForEach(Train.allCases) { train in
            TrainChip(
                train: train,
                selected: session.train == train,
                disabled: session.busy,
                action: { session.selectTrain(train) }
            )
        }
    }
}
