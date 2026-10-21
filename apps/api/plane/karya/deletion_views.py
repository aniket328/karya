# Karya (CWI Studio) — additions to the Plane API. Kept in this package so upstream merges touch one include line.
# SPDX-License-Identifier: AGPL-3.0-only
"""Read and set who may delete work items in a project (see deletion.py for the enforcement)."""

from uuid import UUID

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.views.base import BaseAPIView
from plane.db.models import Project, ProjectMember

from .models import KaryaIssueDeleter


def _deleter_ids(project_id):
    return [str(i) for i in KaryaIssueDeleter.objects.filter(project_id=project_id).values_list("member_id", flat=True)]


class KaryaIssueDeleterEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST])
    def get(self, request, slug, project_id):
        return Response({"member_ids": _deleter_ids(project_id)}, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN])
    def put(self, request, slug, project_id):
        """Body: {"member_ids": ["<user uuid>", ...]}. An empty list restores upstream (admins and creators)."""
        project = Project.objects.filter(pk=project_id, workspace__slug=slug).first()
        if not project:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        raw_ids = request.data.get("member_ids", [])
        if not isinstance(raw_ids, list):
            return Response({"error": "member_ids must be a list"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            wanted = {UUID(str(i)) for i in raw_ids}
        except ValueError:
            return Response({"error": "member_ids must be user ids"}, status=status.HTTP_400_BAD_REQUEST)

        # Only people who can edit work items in this project (admins and members, not guests).
        members = set(
            ProjectMember.objects.filter(
                project_id=project_id, member_id__in=wanted, is_active=True, role__gte=ROLE.MEMBER.value
            ).values_list("member_id", flat=True)
        )
        if wanted - members:
            return Response(
                {"error": "Only active admins or members of this project can delete work items"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            KaryaIssueDeleter.all_objects.filter(project_id=project_id).delete()
            KaryaIssueDeleter.objects.bulk_create(
                [
                    KaryaIssueDeleter(
                        project_id=project_id,
                        workspace_id=project.workspace_id,
                        member_id=member_id,
                        created_by=request.user,
                    )
                    for member_id in members
                ]
            )

        return Response({"member_ids": _deleter_ids(project_id)}, status=status.HTTP_200_OK)
