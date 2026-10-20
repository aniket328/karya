# Karya (CWI Studio) — additions to the Plane API. Kept in this package so upstream merges touch one include line.
# SPDX-License-Identifier: AGPL-3.0-only
from django.apps import AppConfig


class KaryaConfig(AppConfig):
    name = "plane.karya"
    label = "karya"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Connects the Issue pre_save guard for approver-only states.
        from . import approvals  # noqa: F401
