/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
// plane imports
import {
  SUBSCRIPTION_REDIRECTION_URLS,
  SUBSCRIPTION_WITH_BILLING_FREQUENCY,
  TALK_TO_SALES_URL,
} from "@plane/constants";
import { useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { TBillingFrequency } from "@plane/types";
import { EProductSubscriptionEnum } from "@plane/types";
import { getSubscriptionName } from "@plane/utils";
// components
import { DiscountInfo } from "@/components/license/modal/card/discount-info";
import type { TPlanDetail } from "@/components/workspace/billing/comparison/plans";
// Karya
import { KaryaService } from "@/services/karya.service";
// local imports
import { PlanFrequencyToggle } from "./frequency-toggle";

const karyaService = new KaryaService();

type TPlanDetailProps = {
  subscriptionType: EProductSubscriptionEnum;
  planDetail: TPlanDetail;
  billingFrequency: TBillingFrequency | undefined;
  setBillingFrequency: (frequency: TBillingFrequency) => void;
};

export const PlanDetail = observer(function PlanDetail(props: TPlanDetailProps) {
  const { subscriptionType, planDetail, billingFrequency, setBillingFrequency } = props;
  // plane hooks
  const { t } = useTranslation();
  // subscription details
  const subscriptionName = getSubscriptionName(subscriptionType);
  const isSubscriptionActive = planDetail.isActive;
  // pricing details
  const displayPrice = billingFrequency === "month" ? planDetail.monthlyPrice : planDetail.yearlyPrice;
  const pricingDescription = isSubscriptionActive ? "a user per month" : "Quote on request";
  const pricingSecondaryDescription =
    billingFrequency === "month"
      ? planDetail.monthlyPriceSecondaryDescription
      : planDetail.yearlyPriceSecondaryDescription;

  // Karya: no payment gateway yet — "Upgrade" sends CWI Studio a request through the instance SMTP;
  // the mailto redirect stays as the fallback when that fails.
  const { workspaceSlug } = useParams();
  const [isRequesting, setIsRequesting] = useState(false);
  const handleRedirection = async () => {
    const frequency = billingFrequency ?? "year";
    const redirectUrl = SUBSCRIPTION_REDIRECTION_URLS[subscriptionType][frequency] ?? TALK_TO_SALES_URL;
    if (!workspaceSlug) return window.open(redirectUrl, "_blank");
    setIsRequesting(true);
    try {
      const result = await karyaService.requestUpgrade(workspaceSlug.toString(), {
        plan: subscriptionType.toString(),
        frequency: isSubscriptionActive ? frequency : "",
      });
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: result === "already_requested" ? "Request already sent" : "Request sent",
        message: `CWI Studio will contact you about ${subscriptionName} within one working day.`,
      });
    } catch {
      window.open(redirectUrl, "_blank");
    } finally {
      setIsRequesting(false);
    }
  };

  return (
    <div className="col-span-1 flex flex-col justify-between space-y-0.5 p-3">
      {/* Plan name and pricing section */}
      <div className="flex flex-col items-start">
        <div className="flex w-full items-center gap-2 text-h4-semibold">
          <span>{subscriptionName}</span>
          {subscriptionType === EProductSubscriptionEnum.PRO && (
            <span className="rounded-sm bg-accent-primary px-2 py-0.5 text-caption-sm-medium text-on-color">
              Popular
            </span>
          )}
        </div>
        <div className="flex items-start gap-x-2 pb-1 text-tertiary">
          {isSubscriptionActive && displayPrice !== undefined && (
            <div className="flex items-center gap-1 text-h3-semibold text-primary">
              <DiscountInfo
                currency="$"
                frequency={billingFrequency ?? "month"}
                price={displayPrice}
                subscriptionType={subscriptionType}
                className="mr-1.5"
              />
            </div>
          )}
          <div className="pt-1">
            {pricingDescription && <div>{pricingDescription}</div>}
            {pricingSecondaryDescription && (
              <div className="text-caption-xs text-placeholder">{pricingSecondaryDescription}</div>
            )}
          </div>
        </div>
      </div>

      {/* Billing frequency toggle */}
      {SUBSCRIPTION_WITH_BILLING_FREQUENCY.includes(subscriptionType) && billingFrequency && (
        <div className="h-8 py-0.5">
          <PlanFrequencyToggle
            subscriptionType={subscriptionType}
            monthlyPrice={planDetail.monthlyPrice || 0}
            yearlyPrice={planDetail.yearlyPrice || 0}
            selectedFrequency={billingFrequency}
            setSelectedFrequency={setBillingFrequency}
          />
        </div>
      )}

      {/* Subscription button */}
      <div className="flex flex-col items-start gap-1 py-3">
        <Button variant="primary" size="lg" onClick={handleRedirection} loading={isRequesting} className="w-full">
          {isSubscriptionActive ? `Upgrade to ${subscriptionName}` : t("common.upgrade_cta.talk_to_sales")}
        </Button>
      </div>
    </div>
  );
});
