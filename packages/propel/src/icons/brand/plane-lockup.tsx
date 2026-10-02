/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * Karya (CWI Studio) — the mark replaces the upstream logo; export name and props kept so call sites never change.
 */

import * as React from "react";

import type { ISvgIcons } from "../type";

const KARYA_ACCENT = "#ff7a59";

/** Karya lockup: mark + wordmark. The wordmark follows currentColor (theme text), the mark stays coral. */
export function PlaneLockup({ width = "253", height = "53", className, color = "currentColor" }: ISvgIcons) {
  return (
    <svg width={width} height={height} viewBox="0 0 180 53" fill="none" preserveAspectRatio="xMinYMid meet" xmlns="http://www.w3.org/2000/svg" className={className}>
      <g transform="translate(-17 -19) scale(0.92)">
        <rect x="24" y="38" width="36" height="36" rx="9" stroke={KARYA_ACCENT} strokeWidth="5" opacity="0.55" />
        <path d="M33 56L42 65L67 37" stroke={KARYA_ACCENT} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="76" cy="27" r="5" fill={KARYA_ACCENT} />
      </g>
      <text x="66" y="40" fill={color} fontFamily="Inter, 'SF Pro Display', system-ui, sans-serif" fontSize="38" fontWeight="650" letterSpacing="-1">
        Karya
      </text>
    </svg>
  );
}
