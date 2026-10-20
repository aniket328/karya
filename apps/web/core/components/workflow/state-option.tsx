/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import { Combobox } from "@headlessui/react";
import { Lock } from "lucide-react";
import { CheckIcon } from "@plane/propel/icons";
import { Tooltip } from "@plane/propel/tooltip";
import { cn } from "@plane/utils";
// Karya: approver-only states
import { useKaryaStateApprovers } from "@/hooks/karya/use-state-approvers";

export type TStateOptionProps = {
  projectId: string | null | undefined;
  option: {
    value: string | undefined;
    query: string;
    content: React.ReactNode;
  };
  selectedValue: string | null | undefined;
  className?: string;
  filterAvailableStateIds?: boolean;
  isForWorkItemCreation?: boolean;
  alwaysAllowStateChange?: boolean;
};

export const StateOption = observer(function StateOption(props: TStateOptionProps) {
  const { option, className = "", projectId, selectedValue, alwaysAllowStateChange = false } = props;
  // Karya: a state with approvers can only be chosen by one of them
  const { canMoveTo, getRestrictionMessage } = useKaryaStateApprovers(projectId);
  const isLocked =
    !alwaysAllowStateChange && !!option.value && option.value !== selectedValue && !canMoveTo(option.value);

  return (
    <Combobox.Option
      key={option.value}
      value={option.value}
      disabled={isLocked}
      className={({ active, selected }) =>
        cn(
          `${className} ${active && !isLocked ? "bg-layer-transparent-hover" : ""} ${selected ? "text-primary" : "text-secondary"}`,
          { "cursor-not-allowed opacity-60": isLocked }
        )
      }
    >
      {({ selected }) =>
        isLocked ? (
          <Tooltip tooltipContent={getRestrictionMessage(option.value)} position="right">
            <div className="flex w-full items-center justify-between gap-2 truncate">
              <span className="flex-grow truncate">{option.content}</span>
              <Lock className="h-3 w-3 flex-shrink-0 text-placeholder" />
            </div>
          </Tooltip>
        ) : (
          <>
            <span className="flex-grow truncate">{option.content}</span>
            {selected && <CheckIcon className="h-3.5 w-3.5 flex-shrink-0" />}
          </>
        )
      }
    </Combobox.Option>
  );
});
