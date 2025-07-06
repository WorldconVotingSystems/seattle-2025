import jwt
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest
from faker import Faker
from nomnom.nominate.models import NominatingMemberProfile

from seattle_2025_app.auth import ControllBackend, create_member, create_username
from seattle_2025_app.models import ControllPerson

EXISTING_PERID = 42
NEW_PERID = 43
ONLY_NEWPERID = 74
UPDATED_PERID = 321
NEW_NEWPERID = 193
EXISTING_NEWPERID = 6544


@pytest.fixture
def backend():
    return ControllBackend()


def test_authenticate_with_existing_perid(
    db, user_factory, controll_person_factory, backend
):
    # Setup: Create a user and a ControllPerson with a known perid
    user = user_factory()
    controll_person_factory(user=user, perid=EXISTING_PERID)

    # Mock a token with the existing perid
    token = jwt.encode(
        {"perid": EXISTING_PERID}, settings.CONTROLL_JWT_KEY, algorithm="HS256"
    )

    # Run authentication
    authenticated_user = backend.authenticate(None, token=token)

    # Assertions
    assert authenticated_user == user  # Should match the user already in DB


def test_authenticate_updates_perid_with_newperid(
    db, user_factory, controll_person_factory, backend
):
    # Setup: Create a ControllPerson with newperid only
    user = user_factory()
    person = controll_person_factory(user=user, newperid=ONLY_NEWPERID)
    assert person.perid is None

    # Mock a token with both perid and newperid
    token = jwt.encode(
        {"perid": UPDATED_PERID, "newperid": ONLY_NEWPERID},
        settings.CONTROLL_JWT_KEY,
        algorithm="HS256",
    )

    # Run authentication
    authenticated_user = backend.authenticate(None, token=token)

    # Reload record from the database
    person.refresh_from_db()

    # Assertions
    assert authenticated_user == person.user  # Should match the user already in DB
    assert person.perid == UPDATED_PERID  # Ensure perid has been updated
    assert person.newperid == ONLY_NEWPERID  # Should remain unchanged


def test_authenticate_updates_member_id_when_updating_perid(
    db, user_factory, controll_person_factory, backend
):
    user = user_factory(with_convention_profile=True)

    person = controll_person_factory(user=user, newperid=ONLY_NEWPERID)
    assert person.perid is None

    # Mock a token with both perid and newperid
    token = jwt.encode(
        {"perid": UPDATED_PERID, "newperid": ONLY_NEWPERID},
        settings.CONTROLL_JWT_KEY,
        algorithm="HS256",
    )

    # Run authentication
    authenticated_user = backend.authenticate(None, token=token)

    # Reload record from the database
    person.refresh_from_db()

    # Assertions
    assert authenticated_user == person.user  # Should match the user already in DB
    assert authenticated_user.convention_profile.member_number == UPDATED_PERID


def test_authenticate_by_perid_updates_wsfs_rights(
    db, user_factory, controll_person_factory, backend, convention
):
    user = user_factory()

    person = controll_person_factory(user=user, perid=EXISTING_PERID)

    # Mock a token with both perid and newperid
    token = jwt.encode(
        {"perid": EXISTING_PERID, "newperid": None, "rights": "hugo_nominate"},
        settings.CONTROLL_JWT_KEY,
        algorithm="HS256",
    )

    # Run authentication
    authenticated_user = backend.authenticate(None, token=token)

    # Reload record from the database
    person.refresh_from_db()

    # Assertions
    assert authenticated_user == person.user  # Should match the user already in DB
    assert convention.nominating_group in person.user.groups.values_list(
        "name", flat=True
    )


def test_authenticate_by_newperid_updates_wsfs_rights(
    db, user_factory, controll_person_factory, backend, convention
):
    user = user_factory()

    person = controll_person_factory(user=user, newperid=EXISTING_NEWPERID)

    # Mock a token with both perid and newperid
    token = jwt.encode(
        {"perid": None, "newperid": EXISTING_NEWPERID, "rights": "hugo_nominate"},
        settings.CONTROLL_JWT_KEY,
        algorithm="HS256",
    )

    # Run authentication
    authenticated_user = backend.authenticate(None, token=token)

    # Reload record from the database
    person.refresh_from_db()

    # Assertions
    assert authenticated_user == person.user  # Should match the user already in DB
    assert convention.nominating_group in person.user.groups.values_list(
        "name", flat=True
    )


def test_authenticate_doesnt_create_new_row_for_perid(db, backend):
    # Mock a token with an unrecognized perid
    token = jwt.encode(
        {"perid": NEW_PERID}, settings.CONTROLL_JWT_KEY, algorithm="HS256"
    )

    # Run authentication
    authenticated_user = backend.authenticate(None, token=token)
    assert authenticated_user is None  # The backend doesn't auto-create in this case

    # Ensure no new database record is created (creation is not performed)
    assert ControllPerson.objects.count() == 0


def test_authenticate_with_existing_newperid(
    db, user_factory, controll_person_factory, backend
):
    # Setup: Create a ControllPerson with a known newperid
    user = user_factory()
    user = controll_person_factory(user=user, newperid=EXISTING_NEWPERID).user

    # Mock a token with the existing newperid
    token = jwt.encode(
        {"newperid": EXISTING_NEWPERID}, settings.CONTROLL_JWT_KEY, algorithm="HS256"
    )

    # Run authentication
    authenticated_user = backend.authenticate(None, token=token)

    # Assertions
    assert authenticated_user == user  # Should match the user already in DB


def test_authenticate_creates_no_row_for_unmatched_newperid_or_perid(db, backend):
    # Mock a token with an unrecognized newperid
    token = jwt.encode(
        {"newperid": NEW_NEWPERID}, settings.CONTROLL_JWT_KEY, algorithm="HS256"
    )

    # Run authentication
    authenticated_user = backend.authenticate(None, token=token)

    # Assertions
    assert authenticated_user is None  # No matching user should be found
    assert ControllPerson.objects.count() == 0  # Ensure no rows are created


def test_invalid_token_handling(db, backend):
    # Mock an invalid token
    invalid_token = "invalid.token.value"

    # Run authentication
    authenticated_user = backend.authenticate(None, token=invalid_token)

    # Assertions
    assert authenticated_user is None  # Should return None for invalid tokens


@pytest.fixture(name="http_request")
def make_request():
    # generate a fake Django request object
    request = HttpRequest()
    request.method = "GET"
    return request


@pytest.fixture(name="decoded_token")
def make_decoded_token():
    return {
        "perid": EXISTING_PERID,
        "newperid": NEW_PERID,
        "email": Faker().email(),
        "rights": "hugo_nominate",
        "fullName": Faker().name(),
        "first_name": Faker().first_name(),
        "last_name": Faker().last_name(),
    }


def test_create_member_with_no_existing_user(db, http_request, decoded_token):
    member: NominatingMemberProfile | None = create_member(http_request, decoded_token)
    assert member is not None

    assert member.user.username == create_username(
        decoded_token["perid"], decoded_token["newperid"]
    )
    assert member.user.email == decoded_token["email"]
    assert member.user.controll_person.perid == decoded_token["perid"]
    assert member.user.controll_person.newperid == decoded_token["newperid"]


def test_create_member_with_no_existing_user_sets_rights(
    db, http_request, decoded_token, convention
):
    member: NominatingMemberProfile | None = create_member(http_request, decoded_token)
    assert member is not None

    assert convention.nominating_group in member.user.groups.values_list(
        "name", flat=True
    )
    assert convention.voting_group not in member.user.groups.values_list(
        "name", flat=True
    )


def test_create_member_with_existing_user(db, http_request, decoded_token):
    UserModel = get_user_model()

    existing_user = UserModel.objects.create(
        username=create_username(decoded_token["perid"], decoded_token["newperid"]),
        email=decoded_token["email"],
    )

    member: NominatingMemberProfile | None = create_member(http_request, decoded_token)
    assert member is not None

    assert member.user == existing_user
    assert member.user.controll_person.perid == decoded_token["perid"]
    assert member.user.controll_person.newperid == decoded_token["newperid"]


def test_create_member_with_existing_user_updates_rights(
    db, http_request, decoded_token, convention
):
    UserModel = get_user_model()

    existing_user = UserModel.objects.create(
        username=create_username(decoded_token["perid"], decoded_token["newperid"]),
        email=decoded_token["email"],
    )
    existing_user.groups.add(Group.objects.get(name=convention.voting_group))
    existing_user.groups.add(Group.objects.get(name=convention.nominating_group))

    member: NominatingMemberProfile | None = create_member(http_request, decoded_token)
    assert member is not None

    assert convention.nominating_group in member.user.groups.values_list(
        "name", flat=True
    )
    assert convention.voting_group not in member.user.groups.values_list(
        "name", flat=True
    )
