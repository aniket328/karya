# Karya (CWI Studio) — approver-only states.
# SPDX-License-Identifier: AGPL-3.0-only
"""Contract tests for approver-only states (plane/karya/approvals.py).

EdZen board, 21 Oct 2026: developers may move a work item as far as In Review; only named business people may move it
to Done. Every write path must refuse the move: the web app's PATCH and POST, and the public API v1.
"""

from uuid import uuid4

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from plane.db.models import Issue, IssueAssignee, Project, ProjectMember, State, User, WorkspaceMember
from plane.db.models.api import APIToken
from plane.karya.models import KaryaStateApprover

ISSUE_URL = "/api/workspaces/{slug}/projects/{project_id}/issues/{issue_id}/"
ISSUES_URL = "/api/workspaces/{slug}/projects/{project_id}/issues/"
V1_ISSUE_URL = "/api/v1/workspaces/{slug}/projects/{project_id}/work-items/{issue_id}/"
APPROVERS_URL = "/api/workspaces/{slug}/projects/{project_id}/karya/state-approvers/"


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
def states(project, workspace):
    def make(name, group, sequence):
        return State.objects.create(
            name=name, group=group, color="#000000", sequence=sequence, project=project, workspace=workspace
        )

    return {
        "todo": make("Todo", "unstarted", 1000),
        "progress": make("In Progress", "started", 2000),
        "review": make("In Review", "started", 3000),
        "done": make("Done", "completed", 4000),
    }


@pytest.fixture
def developer(workspace, project):
    return _user(workspace, project, 15, "developer")


@pytest.fixture
def business(workspace, project):
    return _user(workspace, project, 15, "business")


@pytest.fixture
def approvers(project, workspace, states, business):
    KaryaStateApprover.objects.create(state=states["done"], approver=business, project=project, workspace=workspace)


def _issue(project, workspace, state, author):
    issue = Issue(name="Fee receipt PDF", project=project, workspace=workspace, state=state)
    issue.save(created_by_id=author.id)
    return issue


def _state_of(issue):
    return Issue.objects.filter(pk=issue.pk).values_list("state_id", flat=True).first()


@pytest.mark.contract
class TestApproverOnlyStateGuard:
    @pytest.mark.django_db
    def test_developer_cannot_move_review_to_done(self, workspace, project, states, developer, approvers):
        issue = _issue(project, workspace, states["review"], developer)
        url = ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        response = _client(developer).patch(url, {"state_id": str(states["done"].id)}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "KARYA_STATE_APPROVAL_REQUIRED"
        assert "business" in response.data["error"] and "Done" in response.data["error"]
        assert _state_of(issue) == states["review"].id

    @pytest.mark.django_db
    def test_refused_move_changes_nothing_else(self, workspace, project, states, developer, business, approvers):
        issue = _issue(project, workspace, states["review"], developer)
        url = ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        response = _client(developer).patch(
            url, {"state_id": str(states["done"].id), "assignee_ids": [str(business.id)], "name": "x"}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not IssueAssignee.objects.filter(issue=issue).exists()
        assert Issue.objects.get(pk=issue.pk).name == "Fee receipt PDF"

    @pytest.mark.django_db
    def test_developer_can_move_to_review(self, workspace, project, states, developer, approvers):
        issue = _issue(project, workspace, states["progress"], developer)
        url = ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        response = _client(developer).patch(url, {"state_id": str(states["review"].id)}, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT, response.data
        assert _state_of(issue) == states["review"].id

    @pytest.mark.django_db
    def test_approver_can_move_review_to_done(self, workspace, project, states, developer, business, approvers):
        issue = _issue(project, workspace, states["review"], developer)
        url = ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        response = _client(business).patch(url, {"state_id": str(states["done"].id)}, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT, response.data
        assert _state_of(issue) == states["done"].id

    @pytest.mark.django_db
    def test_project_admin_is_not_an_approver_by_role(self, workspace, project, states, create_user, approvers):
        issue = _issue(project, workspace, states["review"], create_user)
        url = ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        response = _client(create_user).patch(url, {"state_id": str(states["done"].id)}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert _state_of(issue) == states["review"].id

    @pytest.mark.django_db
    def test_developer_can_edit_a_done_item_without_moving_it(self, workspace, project, states, developer, approvers):
        issue = _issue(project, workspace, states["done"], developer)
        url = ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        response = _client(developer).patch(url, {"name": "Renamed", "state_id": str(states["done"].id)}, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT, response.data
        assert Issue.objects.get(pk=issue.pk).name == "Renamed"

    @pytest.mark.django_db
    def test_developer_can_reopen_a_done_item(self, workspace, project, states, developer, approvers):
        issue = _issue(project, workspace, states["done"], developer)
        url = ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        response = _client(developer).patch(url, {"state_id": str(states["progress"].id)}, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT, response.data

    @pytest.mark.django_db
    def test_developer_cannot_create_an_item_directly_in_done(self, workspace, project, states, developer, approvers):
        url = ISSUES_URL.format(slug=workspace.slug, project_id=project.id)

        response = _client(developer).post(
            url, {"name": "Born done", "state_id": str(states["done"].id)}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Issue.objects.filter(project=project, name="Born done").exists()

    @pytest.mark.django_db
    def test_unrestricted_project_is_unchanged(self, workspace, project, states, developer):
        issue = _issue(project, workspace, states["review"], developer)
        url = ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        response = _client(developer).patch(url, {"state_id": str(states["done"].id)}, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT, response.data

    @pytest.mark.django_db
    def test_public_api_v1_is_guarded(self, workspace, project, states, developer, approvers):
        issue = _issue(project, workspace, states["review"], developer)
        token = APIToken.objects.create(user=developer, label="dev", token=f"plane_api_{uuid4().hex}")
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=token.token)
        url = V1_ISSUE_URL.format(slug=workspace.slug, project_id=project.id, issue_id=issue.id)

        response = client.patch(url, {"state": str(states["done"].id)}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert _state_of(issue) == states["review"].id

    @pytest.mark.django_db
    def test_jobs_without_a_request_user_are_not_blocked(self, workspace, project, states, developer, approvers):
        issue = _issue(project, workspace, states["review"], developer)
        issue.state = states["done"]
        issue.save()  # e.g. the auto-close automation

        assert _state_of(issue) == states["done"].id


@pytest.mark.contract
class TestStateApproverEndpoint:
    @pytest.mark.django_db
    def test_any_member_can_read(self, workspace, project, states, developer, business, approvers):
        url = APPROVERS_URL.format(slug=workspace.slug, project_id=project.id)

        response = _client(developer).get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["states"] == {str(states["done"].id): [str(business.id)]}

    @pytest.mark.django_db
    def test_member_cannot_set(self, workspace, project, states, developer):
        url = APPROVERS_URL.format(slug=workspace.slug, project_id=project.id)

        response = _client(developer).put(
            url, {"state_id": str(states["done"].id), "approver_ids": [str(developer.id)]}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not KaryaStateApprover.objects.exists()

    @pytest.mark.django_db
    def test_admin_sets_replaces_and_clears(self, workspace, project, states, create_user, developer, business):
        url = APPROVERS_URL.format(slug=workspace.slug, project_id=project.id)
        admin = _client(create_user)
        done = str(states["done"].id)

        assert admin.put(url, {"state_id": done, "approver_ids": [str(developer.id)]}, format="json").status_code == 200
        response = admin.put(url, {"state_id": done, "approver_ids": [str(business.id)]}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert set(KaryaStateApprover.objects.values_list("approver_id", flat=True)) == {business.id}

        assert admin.put(url, {"state_id": done, "approver_ids": []}, format="json").status_code == 200
        assert not KaryaStateApprover.all_objects.exists()

    @pytest.mark.django_db
    def test_guests_and_outsiders_cannot_be_approvers(self, workspace, project, states, create_user):
        guest = _user(workspace, project, 5, "guest")
        outsider = User.objects.create(email=f"out-{uuid4().hex[:6]}@karya.test", username=f"out_{uuid4().hex[:6]}")
        url = APPROVERS_URL.format(slug=workspace.slug, project_id=project.id)

        for user in (guest, outsider):
            response = _client(create_user).put(
                url, {"state_id": str(states["done"].id), "approver_ids": [str(user.id)]}, format="json"
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_state_from_another_project_is_refused(self, workspace, project, create_user):
        other = Project.objects.create(name="Other", identifier="OTH", workspace=workspace, created_by=create_user)
        foreign = State.objects.create(name="Done", group="completed", color="#000", project=other, workspace=workspace)
        url = APPROVERS_URL.format(slug=workspace.slug, project_id=project.id)

        response = _client(create_user).put(url, {"state_id": str(foreign.id), "approver_ids": []}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
