/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";

// Karya: upstream shows Plane's customer logos here (Zerodha, Sony, Dolby, Accenture). They are Plane's customers,
// not ours, so the strip is removed — never put another company's logo on a Karya screen without their consent.
export function AuthFooter() {
  return (
    <div className="flex flex-col items-center gap-6">
      <span className="text-13 whitespace-nowrap text-tertiary">Karya by CWI Studio</span>
    </div>
  );
}
