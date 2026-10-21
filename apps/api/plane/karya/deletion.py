# Karya (CWI Studio) — additions to the Plane API. Kept in this package so upstream merges touch one include line.
# SPDX-License-Identifier: AGPL-3.0-only
"""Who may delete work items (EdZen, 22 Oct 2026: everyone creates tickets, only named people delete them).

A project with no deleters keeps upstream behaviour: project admins, and the creator of the work item. A project with
deleters lets exactly those people delete, any work item, and nobody else, admins included.

The views call check_delete() (it also grants: a listed member may delete a work item they did not create). The Issue
pre_save receiver is the backstop for any other path that soft-deletes through the model, e.g. intake. Jobs with no
request user (project deletion cascade, manage.py shell) are not blocked."""

from crum import get_current_user
from django.db.models.signals import pre_save
from django.dispatch import receiver
from rest_framework.exceptions import PermissionDenied

from plane.db.models import Issue, ProjectMember, User, WorkspaceMember

from .models import KaryaIssueDeleter

ERROR_CODE = "KARYA_DELETE_NOT_ALLOWED"
# Kept word for word: the web app maps this upstream message to its permission toast.
UPSTREAM_DENIAL = "Only admin or creator can delete the work item"


def deleter_ids(project_id):
    return set(KaryaIssueDeleter.objects.filter(project_id=project_id).values_list("member_id", flat=True))


def denial_message(deleters):
    names = sorted(
        (u.display_name or u.first_name or u.email)
        for u in User.objects.filter(id__in=deleters).only("display_name", "first_name", "email")
    )
    return f"Only {', '.join(names) or 'named people'} can delete work items in this project."


def _is_project_admin(user, project_id):
    """Upstream's rule from allow_permission([ROLE.ADMIN]): a project admin, or a workspace admin in the project."""
    member = ProjectMember.objects.filter(project_id=project_id, member=user, is_active=True).first()
    if member is None:
        return False
    return (
        member.role == 20
        or WorkspaceMember.objects.filter(
            workspace_id=member.workspace_id, member=user, role=20, is_active=True
        ).exists()
    )


def check_delete(issue, user):
    """Raise PermissionDenied unless `user` may delete `issue`."""
    deleters = deleter_ids(issue.project_id)
    if deleters:
        if user.id in deleters:
            return
        raise PermissionDenied({"error": denial_message(deleters), "code": ERROR_CODE})
    if issue.created_by_id == user.id or _is_project_admin(user, issue.project_id):
        return
    raise PermissionDenied({"error": UPSTREAM_DENIAL})


def check_deleter_list(project_id, user):
    """With deleters set, refuse anyone not on the list (bulk delete, and the pre_save backstop)."""
    deleters = deleter_ids(project_id)
    if deleters and user.id not in deleters:
        raise PermissionDenied({"error": denial_message(deleters), "code": ERROR_CODE})


@receiver(pre_save, sender=Issue, dispatch_uid="karya_guard_issue_deleters")
def guard_issue_deleters(sender, instance, raw=False, **kwargs):
    if raw or instance.deleted_at is None or instance._state.adding:
        return
    user = get_current_user()
    if user is None or user.is_anonymous:
        return
    if Issue.all_objects.filter(pk=instance.pk, deleted_at__isnull=True).exists():
        check_deleter_list(instance.project_id, user)  # being deleted now; only the list restricts here
