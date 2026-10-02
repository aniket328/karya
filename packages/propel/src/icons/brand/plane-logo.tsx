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

/** Karya mark: a task box, the check that closes it, and the next node it heads for. */
export function PlaneLogo({ width = "52", height = "52", className, color = "currentColor" }: ISvgIcons) {
  // the mark keeps its brand colour unless a caller passes an explicit colour
  const c = color === "currentColor" ? KARYA_ACCENT : color;
  return (
    <svg width={width} height={height} viewBox="18 20 66 60" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="24" y="38" width="36" height="36" rx="9" stroke={c} strokeWidth="5" opacity="0.55" />
      <path d="M33 56L42 65L67 37" stroke={c} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="76" cy="27" r="5" fill={c} />
    </svg>
  );
}
