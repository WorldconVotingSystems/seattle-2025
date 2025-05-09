from typing import cast

import jwt
import sentry_sdk
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AbstractUser, Group
from django.db import transaction
from django.db.models import ObjectDoesNotExist
from django.http import HttpRequest
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
        rights = token.get("rights", "").split(",")
        if perid:
            matches = ControllPerson.objects.filter(perid=perid)
            if matched_person := matches.first():
                # update permissions for the user.
                user = matched_person.user
                changed = update_wsfs_permissions(request, rights, user)
                if changed:
                    user.save()
                return user

            if newperid:
                matches = ControllPerson.objects.filter(newperid=newperid)
                if matched_person := matches.first():
                    matched_person.perid = perid
                    matched_person.save()

                    # we also need to update the member number.
                    try:
                        convention_profile = matched_person.user.convention_profile
                        convention_profile.member_number = perid
                        convention_profile.save()

                    except ObjectDoesNotExist:
                        pass

                    return matched_person.user

            # we don't perform creation in this, just lookups. We only save the perid
            # for faster searches later.

        elif newperid:
            matches = ControllPerson.objects.filter(newperid=newperid)
            if matched_person := matches.first():
                user = matched_person.user
                changed = update_wsfs_permissions(request, rights, user)
                if changed:
                    user.save()
                return user

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

    user, created = UserModel.objects.get_or_create(
        username=create_username(perid, newperid),
        defaults=dict(
            email=email,
            first_name=first_name,
            last_name=last_name,
        ),
    )

    # I know this will always be so, but the type checker doesn't.
    user = cast(AbstractUser, user)

    sentry_sdk.set_user(user_info_from_user(user))

    # is the user complete? We need a ControllPerson and NominatingMemberProfile
    # even if we didn't create the user.
    missing_controll_person = False
    missing_convention_profile = False
    if not created:
        try:
            user.controll_person  # type: ignore[reportAttributeAccessIssue]
        except ObjectDoesNotExist:
            missing_controll_person = True

        try:
            user.convention_profile  # type: ignore[reportAttributeAccessIssue]
        except ObjectDoesNotExist:
            missing_convention_profile = True

    if created or missing_controll_person:
        ControllPerson.objects.create(
            perid=perid,
            newperid=newperid,
            user=user,
        )

    if created or missing_convention_profile:
        member = nominate.NominatingMemberProfile.objects.create(
            user=user,
            preferred_name=full_name,
            member_number=member_number,
        )
    else:
        member = user.convention_profile  # type: ignore[reportAttributeAccessIssue]

    # now we check for the rights, and assign the member to the right groups.
    changed = update_wsfs_permissions(request, rights, user)

    if changed:
        user.save()

    return member


def update_wsfs_permissions(
    request: HttpRequest, rights: list[str], user: AbstractUser
) -> bool:
    changed = False

    convention = svcs_from(request).get(ConventionConfiguration)

    groups = Group.objects.filter(
        name__in=[convention.nominating_group, convention.voting_group]
    )
    groups_by_name = {group.name: group for group in groups}
    groups_by_right: dict[str, Group] = {
        "hugo_nominate": groups_by_name[convention.nominating_group],
        "hugo_vote": groups_by_name[convention.voting_group],
    }

    user_group_names = user.groups.values_list("name", flat=True)

    for right, group in groups_by_right.items():
        if right in rights and group.name not in user_group_names:
            user.groups.add(group)
            changed = changed or True
        elif right not in rights and group.name in user_group_names:
            user.groups.remove(group)
            changed = changed or True

    return changed


def user_info_from_user(user: AbstractUser):
    return {
        "id": str(user.pk),
        "email": user.email,
        "username": user.username,
    }
