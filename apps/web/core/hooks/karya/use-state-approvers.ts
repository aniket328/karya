/**
 * Karya (CWI Studio) — approver-only states: who may move work items into which state.
 * The API enforces it on every write (apps/api/plane/karya/approvals.py); this hook only lets the UI say so up front.
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { useCallback } from "react";
import { useParams } from "next/navigation";
import useSWR from "swr";
// hooks
import { useMember } from "@/hooks/store/use-member";
import { useUser } from "@/hooks/store/user";
// services
import type { TKaryaStateApprovers } from "@/services/karya.service";
import { KaryaService } from "@/services/karya.service";

const karyaService = new KaryaService();

export const KARYA_STATE_APPROVERS = (projectId: string) => `KARYA_STATE_APPROVERS_${projectId.toUpperCase()}`;

const EMPTY: TKaryaStateApprovers = {};

export const useKaryaStateApprovers = (projectId: string | null | undefined) => {
  const { workspaceSlug } = useParams();
  const { data: currentUser } = useUser();
  const { getUserDetails } = useMember();

  const { data, mutate } = useSWR(
    workspaceSlug && projectId ? KARYA_STATE_APPROVERS(projectId) : null,
    workspaceSlug && projectId ? () => karyaService.getStateApprovers(workspaceSlug.toString(), projectId) : null,
    { revalidateOnFocus: false, dedupingInterval: 30_000 }
  );
  const approversByState = data ?? EMPTY;

  const getApproverIds = useCallback(
    (stateId: string | null | undefined) => (stateId && approversByState[stateId]) || [],
    [approversByState]
  );

  /** True when the current user may move a work item into this state. */
  const canMoveTo = useCallback(
    (stateId: string | null | undefined) => {
      const ids = getApproverIds(stateId);
      return ids.length === 0 || (!!currentUser?.id && ids.includes(currentUser.id));
    },
    [getApproverIds, currentUser?.id]
  );

  /** "Only Asha, Ravi can move work items here." */
  const getRestrictionMessage = useCallback(
    (stateId: string | null | undefined, stateName?: string) => {
      const names = getApproverIds(stateId)
        .map((id) => getUserDetails(id)?.display_name)
        .filter(Boolean)
        .join(", ");
      return `Only ${names || "approvers"} can move work items ${stateName ? `to ${stateName}` : "here"}.`;
    },
    [getApproverIds, getUserDetails]
  );

  const setApprovers = async (stateId: string, approverIds: string[]) => {
    if (!workspaceSlug || !projectId) return;
    const saved = await karyaService.setStateApprovers(workspaceSlug.toString(), projectId, stateId, approverIds);
    await mutate((current) => {
      const next = { ...current };
      if (saved.length) next[stateId] = saved;
      else delete next[stateId];
      return next;
    }, false);
    return saved;
  };

  return { approversByState, getApproverIds, canMoveTo, getRestrictionMessage, setApprovers };
};
