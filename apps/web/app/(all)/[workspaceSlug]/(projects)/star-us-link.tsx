/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useTheme } from "next-themes";
// assets
import githubBlackImage from "@/app/assets/logos/github-black.png?url";
import githubWhiteImage from "@/app/assets/logos/github-white.png?url";

export function StarUsOnGitHubLink() {
  // hooks
  const { resolvedTheme } = useTheme();
  const imageSrc = resolvedTheme === "dark" ? githubWhiteImage : githubBlackImage;

  return (
    <a
      aria-label="Karya source code (AGPL-3.0)"
      className="flex flex-shrink-0 items-center gap-1.5 rounded-sm bg-layer-2 px-3 py-1.5"
      href="https://github.com/aniket328/karya"
      target="_blank"
      rel="noopener noreferrer"
    >
      <img src={imageSrc} className="h-4 w-4 object-contain" alt="GitHub Logo" aria-hidden="true" />
      {/* Karya: AGPL §13 — every user can reach the source of the version they use */}
      <span className="hidden text-11 font-medium sm:hidden md:block">Source code</span>
    </a>
  );
}
