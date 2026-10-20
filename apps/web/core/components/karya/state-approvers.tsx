/**
 * Karya (CWI Studio) — project settings > States > Approvals: who may move work items into each state.
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { Lock } from "lucide-react";
import { EIconSize, EUserPermissionsLevel } from "@plane/constants";
import { StateGroupIcon } from "@plane/propel/icons";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { EUserProjectRoles } from "@plane/types";
// components
import { MemberDropdown } from "@/components/dropdowns/member/dropdown";
import { SettingsHeading } from "@/components/settings/heading";
// hooks
import { useKaryaStateApprovers } from "@/hooks/karya/use-state-approvers";
import { useMember } from "@/hooks/store/use-member";
import { useProjectState } from "@/hooks/store/use-project-state";
import { useUserPermissions } from "@/hooks/store/user";

type Props = {
  workspaceSlug: string;
  projectId: string;
};

export const KaryaStateApprovers = observer(function KaryaStateApprovers(props: Props) {
  const { workspaceSlug, projectId } = props;
  const { getProjectStates } = useProjectState();
  const { getUserDetails } = useMember();
  const { allowPermissions } = useUserPermissions();
  const { getApproverIds, setApprovers } = useKaryaStateApprovers(projectId);
  const [savingStateId, setSavingStateId] = useState<string | null>(null);

  const states = getProjectStates(projectId) ?? [];
  const isEditable = allowPermissions(
    [EUserProjectRoles.ADMIN],
    EUserPermissionsLevel.PROJECT,
    workspaceSlug,
    projectId
  );

  const handleChange = async (stateId: string, stateName: string, approverIds: string[]) => {
    setSavingStateId(stateId);
    try {
      await setApprovers(stateId, approverIds);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Approvals updated",
        message: approverIds.length
          ? `Only the chosen people can now move work items to ${stateName}.`
          : `Everyone can move work items to ${stateName} again.`,
      });
    } catch (error) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Could not update approvals",
        message: (error as { error?: string })?.error ?? "Please try again.",
      });
    } finally {
      setSavingStateId(null);
    }
  };

  if (states.length === 0) return null;

  return (
    <div className="mt-10 w-full">
      <SettingsHeading
        variant="h4"
        title="Approvals"
        description="Choose who can move work items into a state, e.g. only the business team can move In Review to Done. Leave a state empty and anyone who can edit work items can move them there."
      />
      <div className="mt-4 flex flex-col divide-y divide-subtle rounded-lg border border-subtle">
        {states.map((state) => {
          const approverIds = getApproverIds(state.id);
          const names = approverIds.map((id) => getUserDetails(id)?.display_name).filter(Boolean);
          return (
            <div key={state.id} className="flex items-center justify-between gap-4 px-4 py-2.5">
              <div className="flex min-w-0 items-center gap-2">
                <StateGroupIcon stateGroup={state.group} color={state.color} size={EIconSize.LG} />
                <span className="truncate text-13 font-medium text-primary">{state.name}</span>
                {approverIds.length > 0 && <Lock className="h-3 w-3 flex-shrink-0 text-placeholder" />}
              </div>
              <div className="flex-shrink-0">
                {isEditable ? (
                  <MemberDropdown
                    projectId={projectId}
                    value={approverIds}
                    onChange={(val) => handleChange(state.id, state.name, val)}
                    multiple
                    disabled={savingStateId === state.id}
                    placeholder="Everyone"
                    buttonVariant="border-with-text"
                    showUserDetails
                    dropdownArrow
                    placement="bottom-end"
                    tooltipContent="Who can move work items here"
                  />
                ) : (
                  <span className="text-13 text-secondary">{names.length ? names.join(", ") : "Everyone"}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});
