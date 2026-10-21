/**
 * Karya (CWI Studio) — calls to the Karya additions in the API (apps/api/plane/karya).
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { API_BASE_URL } from "@plane/constants";
// services
import { APIService } from "@/services/api.service";

export type TKaryaUpgradeRequest = { plan: string; frequency?: string; note?: string };
/** state id -> ids of the people allowed to move work items into it; a state that is absent is open to everyone. */
export type TKaryaStateApprovers = Record<string, string[]>;

export class KaryaService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  /** Mails CWI Studio sales through the instance SMTP. Resolves to "sent" or "already_requested". */
  async requestUpgrade(workspaceSlug: string, payload: TKaryaUpgradeRequest): Promise<string> {
    return this.post(`/api/workspaces/${workspaceSlug}/karya/upgrade-request/`, payload)
      .then((res) => res?.data?.status)
      .catch((err) => {
        throw err?.response?.data;
      });
  }

  /** Who may move work items into each approver-only state of a project. */
  async getStateApprovers(workspaceSlug: string, projectId: string): Promise<TKaryaStateApprovers> {
    return this.get(`/api/workspaces/${workspaceSlug}/projects/${projectId}/karya/state-approvers/`)
      .then((res) => res?.data?.states ?? {})
      .catch((err) => {
        throw err?.response?.data;
      });
  }

  /** Project admins only. An empty list opens the state to everyone again. */
  async setStateApprovers(
    workspaceSlug: string,
    projectId: string,
    stateId: string,
    approverIds: string[]
  ): Promise<string[]> {
    return this.put(`/api/workspaces/${workspaceSlug}/projects/${projectId}/karya/state-approvers/`, {
      state_id: stateId,
      approver_ids: approverIds,
    })
      .then((res) => res?.data?.approver_ids ?? [])
      .catch((err) => {
        throw err?.response?.data;
      });
  }

  /** Who may delete work items in a project; empty means upstream (project admins and the creator). */
  async getDeleters(workspaceSlug: string, projectId: string): Promise<string[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/projects/${projectId}/karya/deleters/`)
      .then((res) => res?.data?.member_ids ?? [])
      .catch((err) => {
        throw err?.response?.data;
      });
  }

  /** Project admins only. An empty list restores upstream behaviour. */
  async setDeleters(workspaceSlug: string, projectId: string, memberIds: string[]): Promise<string[]> {
    return this.put(`/api/workspaces/${workspaceSlug}/projects/${projectId}/karya/deleters/`, {
      member_ids: memberIds,
    })
      .then((res) => res?.data?.member_ids ?? [])
      .catch((err) => {
        throw err?.response?.data;
      });
  }
}
