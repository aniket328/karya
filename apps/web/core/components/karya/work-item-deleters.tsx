/**
 * Karya (CWI Studio) — project settings > Members > Deleting work items: who may delete work items.
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { Trash2 } from "lucide-react";
import { EUserPermissionsLevel } from "@plane/constants";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { EUserProjectRoles } from "@plane/types";
// components
import { MemberDropdown } from "@/components/dropdowns/member/dropdown";
import { SettingsHeading } from "@/components/settings/heading";
// hooks
import { useKaryaWorkItemDeleters } from "@/hooks/karya/use-work-item-deleters";
import { useMember } from "@/hooks/store/use-member";
import { useUserPermissions } from "@/hooks/store/user";

type Props = {
  workspaceSlug: string;
  projectId: string;
};

export const KaryaWorkItemDeleters = observer(function KaryaWorkItemDeleters(props: Props) {
  const { workspaceSlug, projectId } = props;
  const { getUserDetails } = useMember();
  const { allowPermissions } = useUserPermissions();
  const { deleterIds, setDeleters } = useKaryaWorkItemDeleters(projectId);
  const [isSaving, setIsSaving] = useState(false);

  const isEditable = allowPermissions(
    [EUserProjectRoles.ADMIN],
    EUserPermissionsLevel.PROJECT,
    workspaceSlug,
    projectId
  );
  const names = deleterIds.map((id) => getUserDetails(id)?.display_name).filter(Boolean);

  const handleChange = async (memberIds: string[]) => {
    setIsSaving(true);
    try {
      await setDeleters(memberIds);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Delete permission updated",
        message: memberIds.length
          ? "Only the chosen people can now delete work items in this project."
          : "Project admins and creators can delete work items again.",
      });
    } catch (error) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Could not update delete permission",
        message: (error as { error?: string })?.error ?? "Please try again.",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="mt-10 w-full">
      <SettingsHeading
        variant="h4"
        title="Deleting work items"
        description="Choose who can delete work items in this project. Everyone else can still create, edit and archive them. Leave it empty and project admins, and whoever created a work item, can delete it."
      />
      <div className="mt-4 flex items-center justify-between gap-4 rounded-lg border border-subtle px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <Trash2 className="h-4 w-4 flex-shrink-0 text-secondary" />
          <span className="truncate text-13 font-medium text-primary">Can delete work items</span>
        </div>
        <div className="flex-shrink-0">
          {isEditable ? (
            <MemberDropdown
              projectId={projectId}
              value={deleterIds}
              onChange={handleChange}
              multiple
              disabled={isSaving}
              placeholder="Admins and creators"
              buttonVariant="border-with-text"
              showUserDetails
              dropdownArrow
              placement="bottom-end"
              tooltipContent="Who can delete work items"
            />
          ) : (
            <span className="text-13 text-secondary">{names.length ? names.join(", ") : "Admins and creators"}</span>
          )}
        </div>
      </div>
    </div>
  );
});
