// SPDX-License-Identifier: GPL-3.0-or-later
import SwiftUI

struct PrivacyView: View {
    private var policy: String? {
        guard let url = Bundle.main.url(forResource: "PrivacyPolicy", withExtension: "txt") else { return nil }
        return try? String(contentsOf: url, encoding: .utf8)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if let policy {
                Text(verbatim: policy).font(.body).textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
            } else {
                Text("The privacy policy could not be loaded. Please reinstall a complete copy of the app.")
            }
            Link("Valve privacy policy", destination: URL(string: "https://store.steampowered.com/privacy_agreement/")!)
            Link("Privacy policy online", destination: URL(string: "https://github.com/aghjkshdsj/PocketGames-No-J/blob/main/App/Resources/PrivacyPolicy.txt")!)
            Link("Project support", destination: URL(string: "https://github.com/aghjkshdsj/PocketGames-No-J/issues")!)
        }
    }
}
