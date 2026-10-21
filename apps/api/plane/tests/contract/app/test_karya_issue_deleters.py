# Karya (CWI Studio) — who may delete work items.
# SPDX-License-Identifier: AGPL-3.0-only
"""Contract tests for work item deleters (plane/karya/deletion.py).

EdZen board, 22 Oct 2026: everyone creates tickets, only named people delete them. With no deleters a project keeps
upstream behaviour (project admins, and the creator).
"""

from uuid import uuid4

import pytest
from crum import impersonate
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from plane.db.models import Issue, Project, ProjectMember, State, User, WorkspaceMember
from plane.db.models.api import APIToken
from plane.karya.models import KaryaIssueDeleter

ISSUE_URL = "/api/workspaces/{slug}/projects/{project_id}/issues/{issue_id}/"
ISSUES_URL = "/api/workspaces/{slug}/projects/{project_id}/issues/"
BULK_DELETE_URL = "/api/workspaces/{slug}/projects/{project_id}/bulk-delete-issues/"
V1_ISSUE_URL = "/api/v1/workspaces/{slug}/projects/{project_id}/work-items/{issue_id}/"
DELETERS_URL = "/api/workspaces/{slug}/projects/{project_id}/karya/deleters/"


def _user(workspace, project, role, prefix):
    unique = uuid4().hex[:8]
    user = User.objects.create(
        email=f"{prefix}-{unique}@karya.test",
        username=f"{prefix}_{unique}",
        first_name=prefix.title(),
        display_name=prefix,
    )
    WorkspaceMember.objects.create(workspace=workspace, member=user, role=role)
    ProjectMember.objects.create(project=project, member=user, workspace=workspace, role=role)
    return user


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def project(db, workspace, create_user):
    project = Project.objects.create(name="EdZen", identifier="EDZ", workspace=workspace, created_by=create_user)
    ProjectMember.objects.create(project=project, member=create_user, workspace=workspace, role=20)
    return project


@pytest.fixture
def state(project, workspace):
    return State.objects.create(
        name="Todo", group="unstarted", color="#000000", sequence=1000, project=project, workspace=workspace
    )


@pytest.fixture
def developer(workspace, project):
    return _user(workspace, project, 15, "developer")


@pytest.fixture
def business(workspace, project):
    return _user(workspace, project, 15, "business")


@pytest.fixture
def deleters(project, workspace, business):
    KaryaIssueDeleter.objects.create(project=project, workspace=workspace, member=business)


def _issue(project, workspace, state, author):
    issue = Issue(name="Fee receipt PDF", project=project, workspace=workspace, state=state)
    issue.save(created_by_id=author.id)
    return issue


def _alive(issue):
    return Issue.objects.filter(pk=issue.pk).exists()


def _delete(user, workspace, project, issue):
    url = ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)
    return _client(user).delete(url)


@pytest.mark.contract
class TestUpstreamRuleWithoutDeleters:
    @pytest.mark.django_db
    def test_creator_can_delete_own_item(self, workspace, project, state, developer):
        issue = _issue(project, workspace, state, developer)

        assert _delete(developer, workspace, project, issue).status_code == status.HTTP_204_NO_CONTENT
        assert not _alive(issue)

    @pytest.mark.django_db
    def test_member_cannot_delete_someone_elses_item(self, workspace, project, state, developer, business):
        issue = _issue(project, workspace, state, business)

        response = _delete(developer, workspace, project, issue)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error"] == "Only admin or creator can delete the work item"
        assert _alive(issue)

    @pytest.mark.django_db
    def test_admin_can_delete_any_item(self, workspace, project, state, create_user, developer):
        issue = _issue(project, workspace, state, developer)

        assert _delete(create_user, workspace, project, issue).status_code == status.HTTP_204_NO_CONTENT
        assert not _alive(issue)


@pytest.mark.contract
class TestDeleters:
    @pytest.mark.django_db
    def test_developer_cannot_delete_own_item(self, workspace, project, state, developer, deleters):
        issue = _issue(project, workspace, state, developer)

        response = _delete(developer, workspace, project, issue)

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "KARYA_DELETE_NOT_ALLOWED"
        assert "business" in response.data["error"]
        assert _alive(issue)

    @pytest.mark.django_db
    def test_developer_can_still_create(self, workspace, project, state, developer, deleters):
        url = ISSUES_URL.format(slug=workspace.slug, project_id=project.id)

        response = _client(developer).post(url, {"name": "New ticket", "state_id": str(state.id)}, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data

    @pytest.mark.django_db
    def test_listed_member_can_delete_someone_elses_item(
        self, workspace, project, state, developer, business, deleters
    ):
        issue = _issue(project, workspace, state, developer)

        assert _delete(business, workspace, project, issue).status_code == status.HTTP_204_NO_CONTENT
        assert not _alive(issue)

    @pytest.mark.django_db
    def test_admin_not_on_the_list_cannot_delete(self, workspace, project, state, create_user, developer, deleters):
        issue = _issue(project, workspace, state, developer)

        response = _delete(create_user, workspace, project, issue)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert _alive(issue)

    @pytest.mark.django_db
    def test_bulk_delete_needs_the_list(self, workspace, project, state, create_user, developer, deleters):
        issue = _issue(project, workspace, state, developer)
        url = BULK_DELETE_URL.format(slug=workspace.slug, project_id=project.id)

        response = _client(create_user).delete(url, {"issue_ids": [str(issue.id)]}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert _alive(issue)

        KaryaIssueDeleter.objects.create(project=project, workspace=workspace, member=create_user)
        response = _client(create_user).delete(url, {"issue_ids": [str(issue.id)]}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert not _alive(issue)

    @pytest.mark.django_db
    def test_public_api_v1_is_guarded(self, workspace, project, state, developer, business, deleters):
        issue = _issue(project, workspace, state, developer)
        url = V1_ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        def v1(user):
            token = APIToken.objects.create(user=user, label="t", token=f"plane_api_{uuid4().hex}")
            client = APIClient()
            client.credentials(HTTP_X_API_KEY=token.token)
            return client

        assert v1(developer).delete(url).status_code == status.HTTP_403_FORBIDDEN
        assert _alive(issue)
        assert v1(business).delete(url).status_code == status.HTTP_204_NO_CONTENT
        assert not _alive(issue)

    @pytest.mark.django_db
    def test_model_backstop_refuses_other_paths(self, workspace, project, state, developer, deleters):
        issue = _issue(project, workspace, state, developer)

        with impersonate(developer), pytest.raises(PermissionDenied):
            issue.delete()

        assert _alive(issue)

    @pytest.mark.django_db
    def test_jobs_without_a_request_user_are_not_blocked(self, workspace, project, state, developer, deleters):
        issue = _issue(project, workspace, state, developer)

        issue.delete()  # e.g. the project-deletion cascade

        assert not _alive(issue)


@pytest.mark.contract
class TestDeleterEndpoint:
    @pytest.mark.django_db
    def test_any_member_can_read(self, workspace, project, developer, business, deleters):
        url = DELETERS_URL.format(slug=workspace.slug, project_id=project.id)

        response = _client(developer).get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["member_ids"] == [str(business.id)]

    @pytest.mark.django_db
    def test_member_cannot_set(self, workspace, project, developer):
        url = DELETERS_URL.format(slug=workspace.slug, project_id=project.id)

        response = _client(developer).put(url, {"member_ids": [str(developer.id)]}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not KaryaIssueDeleter.objects.exists()

    @pytest.mark.django_db
    def test_admin_sets_replaces_and_clears(self, workspace, project, create_user, developer, business):
        url = DELETERS_URL.format(slug=workspace.slug, project_id=project.id)
        admin = _client(create_user)

        assert admin.put(url, {"member_ids": [str(developer.id)]}, format="json").status_code == 200
        response = admin.put(url, {"member_ids": [str(business.id), str(create_user.id)]}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data["member_ids"]) == {str(business.id), str(create_user.id)}
        assert set(KaryaIssueDeleter.objects.values_list("member_id", flat=True)) == {business.id, create_user.id}

        assert admin.put(url, {"member_ids": []}, format="json").status_code == 200
        assert not KaryaIssueDeleter.all_objects.exists()

    @pytest.mark.django_db
    def test_guests_and_outsiders_cannot_be_deleters(self, workspace, project, create_user):
        guest = _user(workspace, project, 5, "guest")
        outsider = User.objects.create(email=f"out-{uuid4().hex[:6]}@karya.test", username=f"out_{uuid4().hex[:6]}")
        url = DELETERS_URL.format(slug=workspace.slug, project_id=project.id)

        for user in (guest, outsider):
            response = _client(create_user).put(url, {"member_ids": [str(user.id)]}, format="json")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not KaryaIssueDeleter.objects.exists()
