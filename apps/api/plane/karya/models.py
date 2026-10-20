# Karya (CWI Studio) — additions to the Plane API. Kept in this package so upstream merges touch one include line.
# SPDX-License-Identifier: AGPL-3.0-only
from django.conf import settings
from django.db import models
from django.db.models import Q

from plane.db.models.project import ProjectBaseModel


class KaryaStateApprover(ProjectBaseModel):
    """A person allowed to move work items into an approver-only state.

    A state with no rows is open to everyone (upstream behaviour). A state with rows accepts a move only from one of
    these people, e.g. "In Review -> Done is for the business team".
    """

    state = models.ForeignKey("db.State", on_delete=models.CASCADE, related_name="karya_approvers")
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="karya_state_approvals"
    )

    class Meta:
        verbose_name = "Karya State Approver"
        verbose_name_plural = "Karya State Approvers"
        db_table = "karya_state_approvers"
        constraints = [
            models.UniqueConstraint(
                fields=["state", "approver"],
                condition=Q(deleted_at__isnull=True),
                name="karya_state_approver_unique_when_deleted_at_null",
            )
        ]

    def __str__(self):
        return f"{self.approver_id} -> {self.state_id}"
