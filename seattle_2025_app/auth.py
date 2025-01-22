import jwt
import sentry_sdk
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AbstractUser, Group
from django.db import transaction
from django_svcs.apps import svcs_from
from nomnom.convention import ConventionConfiguration
from nomnom.nominate import models as nominate

from seattle_2025_app.models import ControllPerson


def create_username(perid: str | None, newperid: str | None) -> str:
    """Define the user name for a member.

    This is _very_ specific to ConTroll; these users are permanently
    bound to it by this format, so we make that explicit in the username.
    """
    perid = perid or "xxx"
    newperid = newperid or "xxx"
    return f"controll:{perid}:{newperid}"


class ControllBackend(BaseBackend):
    def authenticate(self, request, token=None, **kwargs) -> AbstractUser | None:
        if token is None:
            return

        try:
            token = jwt.decode(
                token,
                settings.CONTROLL_JWT_KEY,
                algorithms=["HS256", "HS512"],
                options={"verify_exp": False},
            )
        except jwt.InvalidTokenError as e:
            sentry_sdk.capture_exception(e)
            return None

        # existing user?
        matches = ControllPerson.objects.filter(
            perid=token.get("perid"), newperid=token.get("newperid")
        )
        if matches.exists():
            return matches.first().user
        else:
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None


@transaction.atomic
def create_member(
    request, token: dict[str, str]
) -> nominate.NominatingMemberProfile | None:
    convention = svcs_from(request).get(ConventionConfiguration)
    try:
        perid = token["perid"]
        newperid = token["newperid"]
        email = token["email"]
        first_name = token["first_name"]
        last_name = token["last_name"]
        full_name = token["fullName"]
        rights = token["rights"].split(",")
    except KeyError:
        # the token was incomplete; we can't create a user.
        return None

    if perid is None:
        # we can't create a user without a perid
        return None

    UserModel = get_user_model()

    user = UserModel.objects.create(
        username=create_username(perid, newperid),
        email=email,
        first_name=first_name,
        last_name=last_name,
    )

    ControllPerson.objects.create(
        perid=token.get("perid"),
        newperid=token.get("newperid"),
        user=user,
    )

    member = nominate.NominatingMemberProfile.objects.create(
        user=user,
        preferred_name=full_name,
    )

    # now we check for the rights, and assign the member to the right groups.
    changed = False
    if "hugo_nominate" in rights:
        user.groups.add(Group.objects.get(name=convention.nominating_group))
        changed = changed or True

    if "hugo_vote" in rights:
        user.groups.add(Group.objects.get(name=convention.voting_group))
        changed = changed or True

    if changed:
        user.save()

    return member
