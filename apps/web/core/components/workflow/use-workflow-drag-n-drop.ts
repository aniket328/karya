/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// Karya: upstream ships this as a no-op; we fill it in for approver-only states (hooks/karya/use-state-approvers.ts).
import { useCallback, useState } from "react";
import { useParams } from "next/navigation";
import type { TIssueGroupByOptions } from "@plane/types";
import { useKaryaStateApprovers } from "@/hooks/karya/use-state-approvers";
import { useProjectState } from "@/hooks/store/use-project-state";

export const useWorkFlowFDragNDrop = (groupBy: TIssueGroupByOptions | undefined, subGroupBy?: TIssueGroupByOptions) => {
  const { projectId } = useParams();
  const { canMoveTo, getRestrictionMessage } = useKaryaStateApprovers(projectId?.toString());
  const { getStateById } = useProjectState();
  const [lockedStateId, setLockedStateId] = useState<string | undefined>(undefined);

  /** The state a drop from source to destination would move the work item into, if the move changes its state. */
  const targetState = (
    sourceGroupId: string,
    destinationGroupId: string,
    sourceSubGroupId?: string,
    destinationSubGroupId?: string
  ) => {
    if (groupBy === "state" && sourceGroupId !== destinationGroupId) return destinationGroupId;
    if (subGroupBy === "state" && sourceSubGroupId !== destinationSubGroupId) return destinationSubGroupId;
    return undefined;
  };

  const handleWorkFlowState = useCallback(
    (sourceGroupId: string, destinationGroupId: string, sourceSubGroupId?: string, destinationSubGroupId?: string) => {
      const stateId = targetState(sourceGroupId, destinationGroupId, sourceSubGroupId, destinationSubGroupId);
      setLockedStateId(stateId && !canMoveTo(stateId) ? stateId : undefined);
    },
    // oxlint-disable-next-line eslint-plugin-react-hooks/exhaustive-deps
    [groupBy, subGroupBy, canMoveTo]
  );

  const getIsWorkflowWorkItemCreationDisabled = (groupId: string, subGroupId?: string) => {
    if (groupBy === "state") return !canMoveTo(groupId);
    if (subGroupBy === "state") return !canMoveTo(subGroupId);
    return false;
  };

  return {
    // upstream's red "workflow" overlay hides the text; we show our message instead, so this stays unset
    workflowDisabledSource: undefined,
    isWorkflowDropDisabled: !!lockedStateId,
    workflowDropErrorMessage: lockedStateId
      ? getRestrictionMessage(lockedStateId, getStateById(lockedStateId)?.name)
      : undefined,
    getIsWorkflowWorkItemCreationDisabled,
    handleWorkFlowState,
  };
};
