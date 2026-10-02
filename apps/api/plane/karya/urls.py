# Karya (CWI Studio) — additions to the Plane API. Kept in this package so upstream merges touch one include line.
# SPDX-License-Identifier: AGPL-3.0-only
from django.urls import path

from .views import KaryaUpgradeRequestEndpoint

urlpatterns = [
    path(
        "workspaces/<str:slug>/karya/upgrade-request/",
        KaryaUpgradeRequestEndpoint.as_view(),
        name="karya-upgrade-request",
    ),
]
