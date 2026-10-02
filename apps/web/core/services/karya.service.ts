/**
 * Karya (CWI Studio) — calls to the Karya additions in the API (apps/api/plane/karya).
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { API_BASE_URL } from "@plane/constants";
// services
import { APIService } from "@/services/api.service";

export type TKaryaUpgradeRequest = { plan: string; frequency?: string; note?: string };

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
}
