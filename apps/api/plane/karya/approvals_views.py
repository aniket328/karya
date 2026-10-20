# Karya (CWI Studio) — additions to the Plane API. Kept in this package so upstream merges touch one include line.
# SPDX-License-Identifier: AGPL-3.0-only
"""Read and set who may move work items into each state of a project (see approvals.py for the enforcement)."""

from collections import defaultdict
from uuid import UUID

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.views.base import BaseAPIView
from plane.db.models import ProjectMember, State

from .models import KaryaStateApprover


def _approvers_by_state(project_id):
    result = defaultdict(list)
    rows = KaryaStateApprover.objects.filter(project_id=project_id, state__deleted_at__isnull=True).values_list(
        "state_id", "approver_id"
    )
    for state_id, approver_id in rows:
        result[str(state_id)].append(str(approver_id))
    return result


class KaryaStateApproverEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST])
    def get(self, request, slug, project_id):
        return Response({"states": _approvers_by_state(project_id)}, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN])
    def put(self, request, slug, project_id):
        """Body: {"state_id": "<uuid>", "approver_ids": ["<user uuid>", ...]}. An empty list opens the state to all."""
        state = State.objects.filter(
            pk=request.data.get("state_id"), project_id=project_id, workspace__slug=slug
        ).first()
        if not state:
            return Response({"error": "State not found"}, status=status.HTTP_404_NOT_FOUND)

        raw_ids = request.data.get("approver_ids", [])
        if not isinstance(raw_ids, list):
            return Response({"error": "approver_ids must be a list"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            wanted = {UUID(str(i)) for i in raw_ids}
        except ValueError:
            return Response({"error": "approver_ids must be user ids"}, status=status.HTTP_400_BAD_REQUEST)

        # Only people who can edit work items in this project (admins and members, not guests) can be approvers.
        members = set(
            ProjectMember.objects.filter(
                project_id=project_id, member_id__in=wanted, is_active=True, role__gte=ROLE.MEMBER.value
            ).values_list("member_id", flat=True)
        )
        if wanted - members:
            return Response(
                {"error": "Approvers must be active admins or members of this project"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            KaryaStateApprover.all_objects.filter(state=state).delete()
            KaryaStateApprover.objects.bulk_create(
                [
                    KaryaStateApprover(
                        state=state,
                        approver_id=member_id,
                        project_id=project_id,
                        workspace_id=state.workspace_id,
                        created_by=request.user,
                    )
                    for member_id in members
                ]
            )

        return Response(
            {"state_id": str(state.id), "approver_ids": [str(m) for m in members]}, status=status.HTTP_200_OK
        )
