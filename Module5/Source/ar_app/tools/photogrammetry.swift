// Photogrammetry of my horse statue: the 28 Module 1 photos -> a textured USDZ model.
// Apple's Object Capture (RealityKit PhotogrammetrySession), part of macOS; Apple silicon.
//
// Build:  swiftc -O -swift-version 5 photogrammetry.swift -o photogrammetry
// Run:    ./photogrammetry <photo_dir> <out.usdz> [preview|reduced|medium|full|raw]
// The result has no real-world scale (plain JPGs carry no depth); scan_to_glb.py scales it.
import Foundation
import RealityKit

let args = CommandLine.arguments
let input = URL(fileURLWithPath: args[1], isDirectory: true)
let output = URL(fileURLWithPath: args[2])
let name = args.count > 3 ? args[3] : "medium"
let detail: PhotogrammetrySession.Request.Detail = [
    "preview": .preview, "reduced": .reduced, "medium": .medium, "full": .full, "raw": .raw,
][name] ?? .medium

var config = PhotogrammetrySession.Configuration()
config.featureSensitivity = .high
config.sampleOrdering = .sequential
config.isObjectMaskingEnabled = true

let session = try PhotogrammetrySession(input: input, configuration: config)
let start = Date()
_ = Task {  // the task exits the process itself when processing ends
    var lastPct = -1
    for try await out in session.outputs {
        switch out {
        case .inputComplete: print("input complete")
        case .invalidSample(let id, let reason): print("invalid sample \(id): \(reason)")
        case .skippedSample(let id): print("skipped sample \(id)")
        case .automaticDownsampling: print("automatic downsampling")
        case .requestProgress(_, let f):
            let p = Int(f * 100); if p / 10 != lastPct / 10 { print("progress \(p)%"); lastPct = p }
        case .requestComplete(_, let result): print("request complete: \(result)")
        case .requestError(_, let error): print("request error: \(error)"); exit(1)
        case .processingComplete:
            print(String(format: "processing complete in %.0f s", Date().timeIntervalSince(start))); exit(0)
        case .processingCancelled: print("cancelled"); exit(2)
        default: break
        }
    }
}
try session.process(requests: [.modelFile(url: output, detail: detail)])
RunLoop.main.run()
