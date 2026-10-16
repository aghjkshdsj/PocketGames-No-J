// SPDX-License-Identifier: GPL-3.0-or-later
import SwiftUI

private struct LegalDocument: Decodable, Identifiable {
    let id: String
    let title: String
    let file: String
    let sourceURL: String?
}

private struct LegalIndex: Decodable {
    let documents: [LegalDocument]

    static func load() -> LegalIndex? {
        guard let url = Bundle.main.url(forResource: "index", withExtension: "json", subdirectory: "Legal"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(LegalIndex.self, from: data)
    }
}

private struct LegalBuildInfo: Decodable {
    let revision: String
    let sourceURL: String

    static func load() -> LegalBuildInfo? {
        guard let url = Bundle.main.url(forResource: "build-info", withExtension: "json", subdirectory: "Legal"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(LegalBuildInfo.self, from: data)
    }
}

struct LegalNoticesView: View {
    @ObservedObject private var ui = UIState.shared
    private let index = LegalIndex.load()
    private let buildInfo = LegalBuildInfo.load()

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            DeckCard(title: "PocketGames No J", icon: "doc.text") {
                Text("Maintained by Dan. Third-party copyrights remain with their respective holders.")
                Text("The program is distributed under GPL-3.0-or-later with additional permission. You may redistribute and modify it under those terms. It is provided without warranty, to the extent permitted by law. Individual components retain the licenses reproduced below.")
                    .font(.footnote).foregroundStyle(Deck.dim)
                if let buildInfo, let sourceURL = URL(string: buildInfo.sourceURL) {
                    Link("Source code and build instructions", destination: sourceURL)
                    Text("Source revision: \(buildInfo.revision)")
                        .font(.caption.monospaced()).textSelection(.enabled)
                }
            }
            if let index {
                GlassCard {
                    ForEach(index.documents) { document in
                        Button { ui.open(.licenseDocument(document.id)) } label: {
                            GlassRow(last: document.id == index.documents.last?.id) {
                                Text(document.title).multilineTextAlignment(.leading)
                                Spacer()
                                Image(systemName: "chevron.right").foregroundStyle(Glass.secondary)
                            }
                            .contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                        .padFocus("legal.\(document.id)", radius: 12) { ui.open(.licenseDocument(document.id)) }
                    }
                }
            } else {
                Text("License notices could not be loaded. Please reinstall the app from a complete distribution.")
            }
        }
    }
}

struct LegalDocumentView: View {
    let documentID: String

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if let document = LegalIndex.load()?.documents.first(where: { $0.id == documentID }) {
                Text(document.title).font(.title2.weight(.bold))
                if let text = contents(document) {
                    Text(verbatim: text).font(.footnote).textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                } else {
                    Text("This license document could not be loaded. Please reinstall the app from a complete distribution.")
                }
                if let source = document.sourceURL, let url = URL(string: source) {
                    Link("Original document / source", destination: url)
                }
            } else {
                Text("This license document is unavailable.")
            }
        }
    }

    private func contents(_ document: LegalDocument) -> String? {
        guard !document.file.contains("/"), !document.file.contains("\\"),
              let url = Bundle.main.url(forResource: document.file, withExtension: nil, subdirectory: "Legal") else { return nil }
        return try? String(contentsOf: url, encoding: .utf8)
    }
}
