import random
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from django.contrib.auth import get_user, get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.management import call_command

from seattle_2025_app.models import ControllPerson

UserModel = get_user_model()

cr_full_token = {
    "email": "chris.rose+regtest.full@seattlein2025.org",
    "perid": 1044582,
    "newperid": None,
    "legalName": None,
    "first_name": "Chris",
    "last_name": "Rose",
    "fullName": "Chris Rose",
    "exp": 1737541662,
    "resType": "fullRights",
    "rights": "",
}

syd_full_token = {
    "email": "sydweinstein@gmail.com",
    "perid": 1044580,
    "newperid": 1170,
    "legalName": None,
    "first_name": "syd",
    "last_name": "gmail test",
    "fullName": "syd gmail test",
    "exp": 1737518677,
    "resType": "fullRights",
    "rights": "hugo_nominate,hugo_vote",
}


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "-v3", "all/0001-permissions.json")


@pytest.fixture(name="make_token")
def make_token_func(settings):
    def make_token(payload, key=None) -> str:
        key = settings.CONTROLL_JWT_KEY if key is None else key
        payload.setdefault(
            "exp", (datetime.now(timezone.utc) + timedelta(days=1)).timestamp()
        )
        return jwt.encode(payload, key, "HS512")

    return make_token


def make_controll_user(
    perid: str | None, newperid: str | None = None
) -> ControllPerson:
    user = UserModel.objects.create_user(
        username="johnny",
        email="johnny@onthe.spot",
    )

    person = ControllPerson.objects.create(
        user=user,
        perid=perid,
        newperid=newperid,
    )

    return person


@pytest.fixture
def perid():
    return random.randint(1000000, 9999999)


@pytest.fixture
def newperid():
    return random.randint(1000, 9999)


@pytest.mark.django_db
def test_valid_params_with_existing_member(client, make_token, perid):
    existing_user_payload = dict(**cr_full_token)
    del existing_user_payload["exp"]  # make sure the expiry is valid
    existing_user_payload["perid"] = perid
    existing_user_payload["newperid"] = None

    controll_user = make_controll_user(perid, None)

    existing_user_token = make_token(existing_user_payload)

    response = client.get(
        "/controll-redirect/",
        {"r": existing_user_token},
    )

    assert response.status_code == 302
    assert response.url == "/"
    assert get_user(client) == controll_user.user


@pytest.mark.django_db
def test_valid_params_with_new_member(client, make_token, perid):
    new_user_payload = dict(**cr_full_token)
    del new_user_payload["exp"]  # make sure the expiry is valid
    new_user_payload["perid"] = perid
    new_user_payload["newperid"] = None

    new_user_token = make_token(new_user_payload)

    response = client.get(
        "/controll-redirect/",
        {"r": new_user_token},
    )

    assert response.status_code == 302
    assert response.url == "/"
    assert get_user(client) is not None
    assert not get_user(client).is_anonymous


RIGHTS = [
    (
        "hugo_nominate,hugo_vote",
        True,
        True,
    ),
    (
        "hugo_nominate",
        False,
        True,
    ),
    (
        "hugo_vote",
        True,
        False,
    ),
    (
        "",
        False,
        False,
    ),
    (
        "random bullshit",
        False,
        False,
    ),
    (
        "hugo_nominate,hugo_vote,hugo_vote",
        True,
        True,
    ),
    (
        "hugo_nominate,hugo_nominate",
        False,
        True,
    ),
    (
        "hugo_vote,hugo_vote",
        True,
        False,
    ),
    (
        "hugo_vote,hugo_nominate,random bullshit",
        True,
        True,
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize("rights,can_vote,can_nominate", RIGHTS)
def test_new_member_permission(
    client, make_token, perid, rights, convention, can_vote, can_nominate
):
    new_user_payload = dict(**cr_full_token)
    del new_user_payload["exp"]  # make sure the expiry is valid
    new_user_payload["perid"] = perid
    new_user_payload["newperid"] = None
    new_user_payload["rights"] = rights
    new_user_token = make_token(new_user_payload)

    client.get(
        "/controll-redirect/",
        {"r": new_user_token},
    )

    user: AbstractUser = get_user(client)
    user_group_names = [g.name for g in user.groups.all()]
    assert (convention.nominating_group in user_group_names) == can_nominate
    assert (convention.voting_group in user_group_names) == can_vote


@pytest.mark.django_db
def test_invalid_token(client, make_token):
    token = make_token({}, "not the key")

    response = client.get(
        "/controll-redirect/",
        {"r": token},
    )

    assert response.status_code == 403
