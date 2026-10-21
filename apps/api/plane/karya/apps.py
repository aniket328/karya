# Karya (CWI Studio) — additions to the Plane API. Kept in this package so upstream merges touch one include line.
# SPDX-License-Identifier: AGPL-3.0-only
from django.apps import AppConfig


class KaryaConfig(AppConfig):
    name = "plane.karya"
    label = "karya"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Connect the Issue pre_save guards for approver-only states and work item deleters.
        from . import approvals, deletion  # noqa: F401
