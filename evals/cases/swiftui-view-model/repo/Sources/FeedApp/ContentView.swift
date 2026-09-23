import SwiftUI

struct ContentView: View {
    @State private var items: [FeedItem] = []

    var body: some View {
        List(items) { item in
            Text(item.title)
        }
        .task {
            await loadFeed()
        }
    }

    private func loadFeed() async {
        guard let url = URL(string: "https://example.com/feed") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            items = try JSONDecoder().decode([FeedItem].self, from: data)
        } catch {
            print("failed to load feed: \(error)")
        }
    }
}
