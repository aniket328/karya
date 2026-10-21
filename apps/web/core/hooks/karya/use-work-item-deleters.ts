/**
 * Karya (CWI Studio) — who may delete work items in a project.
 * The API enforces it on every delete (apps/api/plane/karya/deletion.py); this hook only lets the UI say so up front.
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { useCallback } from "react";
import { useParams } from "next/navigation";
import useSWR from "swr";
import { EUserPermissions, EUserPermissionsLevel } from "@plane/constants";
// hooks
import { useMember } from "@/hooks/store/use-member";
import { useUser, useUserPermissions } from "@/hooks/store/user";
// services
import { KaryaService } from "@/services/karya.service";

const karyaService = new KaryaService();

export const KARYA_WORK_ITEM_DELETERS = (projectId: string) => `KARYA_WORK_ITEM_DELETERS_${projectId.toUpperCase()}`;

const EMPTY: string[] = [];

export const useKaryaWorkItemDeleters = (projectId: string | null | undefined) => {
  const { workspaceSlug } = useParams();
  const { data: currentUser } = useUser();
  const { getUserDetails } = useMember();
  const { allowPermissions } = useUserPermissions();

  const { data, mutate } = useSWR(
    workspaceSlug && projectId ? KARYA_WORK_ITEM_DELETERS(projectId) : null,
    workspaceSlug && projectId ? () => karyaService.getDeleters(workspaceSlug.toString(), projectId) : null,
    { revalidateOnFocus: false, dedupingInterval: 30_000 }
  );
  const deleterIds = data ?? EMPTY;

  /** With deleters set only they may delete; otherwise upstream: project admins and the work item's creator. */
  const canDelete = useCallback(
    (createdBy: string | null | undefined) => {
      if (!currentUser?.id) return false;
      if (deleterIds.length) return deleterIds.includes(currentUser.id);
      if (createdBy === currentUser.id) return true;
      return !!allowPermissions(
        [EUserPermissions.ADMIN],
        EUserPermissionsLevel.PROJECT,
        workspaceSlug?.toString(),
        projectId ?? undefined
      );
    },
    [deleterIds, currentUser?.id, allowPermissions, workspaceSlug, projectId]
  );

  /** "Only Asha, Ravi can delete work items in this project." */
  const restrictionMessage = deleterIds.length
    ? `Only ${deleterIds
        .map((id) => getUserDetails(id)?.display_name)
        .filter(Boolean)
        .join(", ")} can delete work items in this project.`
    : "Only project admins and the person who created a work item can delete it.";

  const setDeleters = async (memberIds: string[]) => {
    if (!workspaceSlug || !projectId) return;
    const saved = await karyaService.setDeleters(workspaceSlug.toString(), projectId, memberIds);
    await mutate(saved, false);
    return saved;
  };

  return { deleterIds, canDelete, restrictionMessage, setDeleters };
};
