/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import { useParams, useRouter } from "next/navigation";
// plane imports
import { PlaneLogo } from "@plane/propel/icons";
import { Tooltip } from "@plane/propel/tooltip";
// hooks
import { usePlatformOS } from "@/hooks/use-platform-os";
import packageJson from "package.json";

/**
 * Karya brand tag. Replaces upstream's "Community" edition badge (which opened Plane's paid-plan modal):
 * the Karya mark + name, version on hover, and a click through to the workspace's plans page, where
 * "Upgrade" sends CWI Studio a request.
 */
export const WorkspaceEditionBadge = observer(function WorkspaceEditionBadge() {
  const { workspaceSlug } = useParams();
  const router = useRouter();
  const { isMobile } = usePlatformOS();

  return (
    <Tooltip tooltipContent={`Karya v${packageJson.version} · by CWI Studio`} isMobile={isMobile}>
      <button
        type="button"
        onClick={() => workspaceSlug && router.push(`/${workspaceSlug.toString()}/settings/billing`)}
        aria-label="Karya by CWI Studio — plans"
        className="group flex items-center gap-2 rounded-md px-2 py-1.5 transition-colors hover:bg-layer-transparent-hover"
      >
        <PlaneLogo width="22" height="20" />
        <span className="flex flex-col items-start leading-tight">
          <span className="text-13 font-semibold text-primary">Karya</span>
          <span className="text-10 tracking-wide text-tertiary group-hover:text-secondary">by CWI Studio</span>
        </span>
      </button>
    </Tooltip>
  );
});
