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
    return f"controll.{perid}.{newperid}"


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

        # Algorithm for authentication:
        #
        # if given perid…
        #    look for perid in that table, if found
        #       return id
        #       exit
        #    if also given newperid
        #       look for newperid in that table, if found
        #          update table row to set perid
        #          return id
        #          exit
        #    else
        #       create new row
        #       set perid in that row
        #       return id
        #       exit
        # else given newperid
        #    look for newperid in that table
        #    if round
        #       return id
        #       exit
        #    else
        #       create new row
        #       set newperid in that row
        #       return id
        #       exit

        perid = token.get("perid")
        newperid = token.get("newperid")

        if perid:
            matches = ControllPerson.objects.filter(perid=perid)
            if matches.exists():
                return matches.first().user

            if newperid:
                matches = ControllPerson.objects.filter(newperid=newperid)
                if matches.exists():
                    match = matches.first()
                    match.perid = perid
                    match.save()
                    return match.user

            # we don't perform creation in this, just lookups. We only save the perid
            # for faster searches later.

        elif newperid:
            matches = ControllPerson.objects.filter(newperid=newperid)
            if matches.exists():
                return matches.first().user

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

    if perid is None and newperid is None:
        # we can't create a user without a perid or a newperid
        return None

    UserModel = get_user_model()

    member_number = perid if perid else newperid

    user = UserModel.objects.create(
        username=create_username(perid, newperid),
        email=email,
        first_name=first_name,
        last_name=last_name,
    )

    sentry_sdk.set_user(user_info_from_user(user))

    ControllPerson.objects.create(
        perid=perid,
        newperid=newperid,
        user=user,
    )

    member = nominate.NominatingMemberProfile.objects.create(
        user=user,
        preferred_name=full_name,
        member_number=member_number,
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


def user_info_from_user(user: AbstractUser):
    return {
        "id": str(user.pk),
        "email": user.email,
        "username": user.username,
    }
