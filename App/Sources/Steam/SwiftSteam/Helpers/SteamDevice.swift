// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright 2026 Jfishin, 125hz
// Additional permission: see LICENSE-EXCEPTION.md
//
// author's permission (see docs/STEAM_SIGNIN.md, "Provenance").

import Foundation
#if canImport(UIKit)
import UIKit
#endif

/// Cross-platform device name — `Host.current()` doesn't exist on iOS.
enum SteamDevice {
    static var name: String {
        #if canImport(UIKit)
        return UIDevice.current.name
        #else
        return Host.current().localizedName ?? "SwiftSteam"
        #endif
    }
}
