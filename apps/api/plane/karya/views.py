# Karya (CWI Studio) — additions to the Plane API. Kept in this package so upstream merges touch one include line.
# SPDX-License-Identifier: AGPL-3.0-only
"""Upgrade requests: Karya has no payment gateway yet, so "Upgrade" mails the CWI Studio sales inbox via the instance SMTP."""
import logging
import os

from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import escape
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import WorkspaceUserPermission
from plane.app.views.base import BaseAPIView
from plane.db.models import Workspace, WorkspaceMember
from plane.license.utils.instance_value import get_email_configuration
from plane.utils.exception_logger import log_exception

SALES_EMAIL = os.environ.get("KARYA_SALES_EMAIL", "aniket@cwistudio.in")
PLANS = {"pro", "business", "enterprise", "one"}
FREQUENCIES = {"month", "year", ""}
COOLDOWN_SECONDS = 600


class KaryaUpgradeRequestEndpoint(BaseAPIView):
    permission_classes = [WorkspaceUserPermission]

    def post(self, request, slug):
        plan = str(request.data.get("plan", "")).lower()[:20]
        frequency = str(request.data.get("frequency", "")).lower()[:10]
        if plan not in PLANS or frequency not in FREQUENCIES:
            return Response({"error": "Unknown plan"}, status=status.HTTP_400_BAD_REQUEST)
        workspace = Workspace.objects.filter(slug=slug).first()
        if not workspace:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        key = f"karya:upgrade-request:{workspace.id}:{plan}"
        if cache.get(key):
            return Response({"status": "already_requested"}, status=status.HTTP_200_OK)

        user = request.user
        members = WorkspaceMember.objects.filter(workspace=workspace, is_active=True, member__is_bot=False).count()
        host, smtp_user, password, port, use_tls, use_ssl, sender = get_email_configuration()
        if not host:
            return Response({"error": "Email is not configured"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        rows = [
            ("Workspace", f"{workspace.name} ({workspace.slug})"),
            ("Requested by", f"{user.display_name or user.first_name} <{user.email}>"),
            ("Plan", plan.title()),
            ("Billing", frequency or "not chosen"),
            ("Active members", str(members)),
            ("Note", str(request.data.get("note", ""))[:1000] or "—"),
        ]
        text = "Karya upgrade request\n\n" + "\n".join(f"{k}: {v}" for k, v in rows)
        html = "<h3>Karya upgrade request</h3><table>" + "".join(
            f"<tr><td style='padding:4px 12px 4px 0;color:#78716c'>{escape(k)}</td><td>{escape(v)}</td></tr>" for k, v in rows
        ) + "</table><p>Reply to this email to reach the requester.</p>"
        try:
            connection = get_connection(
                host=host, port=int(port), username=smtp_user, password=password,
                use_tls=use_tls == "1", use_ssl=use_ssl == "1", timeout=15,
            )
            msg = EmailMultiAlternatives(
                subject=f"[Karya] {workspace.name} wants {plan.title()}",
                body=text, from_email=sender, to=[SALES_EMAIL], reply_to=[user.email], connection=connection,
            )
            msg.attach_alternative(html, "text/html")
            msg.send()
        except Exception as e:  # noqa: BLE001 — surface as 502, details to the log
            log_exception(e)
            return Response({"error": "Could not send the request"}, status=status.HTTP_502_BAD_GATEWAY)

        cache.set(key, 1, COOLDOWN_SECONDS)
        logging.getLogger("plane.api").info("karya upgrade request sent", extra={"workspace": workspace.slug, "plan": plan})
        return Response({"status": "sent"}, status=status.HTTP_200_OK)
