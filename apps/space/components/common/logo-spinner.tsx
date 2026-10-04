/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

/**
 * Karya: animated mark replaces upstream's logo GIF. The task box draws, the check closes it, the node pops — then
 * it resets. Inline SVG (SMIL), so no asset, crisp at any size, same coral on light and dark.
 */
const ACCENT = "#ff7a59";
const T = { dur: "1.8s", repeatCount: "indefinite" } as const;

export function LogoSpinner() {
  return (
    <div className="flex items-center justify-center" role="status" aria-label="Loading">
      <svg viewBox="18 20 66 60" fill="none" className="h-6 w-auto sm:h-11" xmlns="http://www.w3.org/2000/svg">
        <rect
          x="24" y="38" width="36" height="36" rx="9" stroke={ACCENT} strokeWidth="5" opacity="0.55"
          strokeDasharray="130" strokeDashoffset="130"
        >
          <animate attributeName="stroke-dashoffset" values="130;0;0;130" keyTimes="0;0.3;0.85;1" {...T} />
        </rect>
        <path
          d="M33 56L42 65L67 37" stroke={ACCENT} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round"
          strokeDasharray="52" strokeDashoffset="52"
        >
          <animate attributeName="stroke-dashoffset" values="52;52;0;0;52" keyTimes="0;0.25;0.5;0.85;1" {...T} />
        </path>
        <circle cx="76" cy="27" r="0" fill={ACCENT}>
          <animate attributeName="r" values="0;0;6;5;5;0" keyTimes="0;0.5;0.58;0.64;0.85;1" {...T} />
        </circle>
      </svg>
    </div>
  );
}
