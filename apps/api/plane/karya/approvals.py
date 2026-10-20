# Karya (CWI Studio) — additions to the Plane API. Kept in this package so upstream merges touch one include line.
# SPDX-License-Identifier: AGPL-3.0-only
"""Approver-only states: only named people may move a work item into a state that has approvers (EdZen, 21 Oct 2026:
developers stop at In Review, the business team moves In Review -> Done).

Enforced on Issue pre_save rather than in the views, so every write path is covered without editing upstream code:
the web app, bulk edits, the public API v1, intake and drafts all save through the model. Jobs with no request user
(auto-close automation, manage.py shell) are not blocked."""

from crum import get_current_user
from django.db.models.signals import pre_save
from django.dispatch import receiver
from rest_framework.exceptions import PermissionDenied

from plane.db.models import Issue, State, User

from .models import KaryaStateApprover

ERROR_CODE = "KARYA_STATE_APPROVAL_REQUIRED"


def approver_ids(state_id):
    return set(KaryaStateApprover.objects.filter(state_id=state_id).values_list("approver_id", flat=True))


def denial_message(state_id, approvers):
    state = State.all_state_objects.filter(pk=state_id).values_list("name", flat=True).first() or "this state"
    names = sorted(
        (u.display_name or u.first_name or u.email)
        for u in User.objects.filter(id__in=approvers).only("display_name", "first_name", "email")
    )
    who = ", ".join(names) if names else "an approver"
    return f"Only {who} can move work items to {state}."


def check_state_change(instance, state_id, user=None):
    """Raise PermissionDenied if `user` (default: the request user) may not move `instance` into `state_id`.
    `instance` is None for a new work item."""
    if not state_id:
        return
    user = user if user is not None else get_current_user()
    if user is None or user.is_anonymous:
        return
    approvers = approver_ids(state_id)
    if not approvers or user.id in approvers:
        return
    if instance is not None and instance.pk and not instance._state.adding:
        previous = Issue.all_objects.filter(pk=instance.pk).values_list("state_id", flat=True).first()
        if previous == state_id:
            return  # the state is not changing; editing a Done item is still allowed
    raise PermissionDenied({"error": denial_message(state_id, approvers), "code": ERROR_CODE})


def check_serializer_state(serializer, attrs):
    """Early check from the issue serializers' validate(), so a refused move changes nothing else in the request
    (upstream saves assignees and labels before the issue itself)."""
    state = attrs.get("state")
    if state is not None:
        check_state_change(serializer.instance, state.id)


@receiver(pre_save, sender=Issue, dispatch_uid="karya_guard_approver_only_states")
def guard_approver_only_states(sender, instance, raw=False, **kwargs):
    if raw:
        return
    check_state_change(instance, instance.state_id)
