// swift-tools-version:6.0
import PackageDescription

let package = Package(
    name: "FeedApp",
    platforms: [.iOS(.v17), .macOS(.v14)],
    targets: [
        .executableTarget(name: "FeedApp")
    ]
)
