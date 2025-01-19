from pprint import pprint
from typing import Any, TypeVar, overload

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Q
from django.http import HttpRequest
from social_core.backends.oauth import BaseOAuth2

UserModel = get_user_model()

V = TypeVar("V")


@overload
def clean_value(v: str) -> str: ...
@overload
def clean_value(v: V) -> V: ...


def clean_value(v: str | V) -> str | V:
    return v.strip() if isinstance(v, str) else v


class ConTrollOAuth2Backend(BaseOAuth2):
    # BASE_URL is dynamic.
    ACCESS_TOKEN_METHOD = "POST"
    REDIRECT_STATE = False
    STATE_PARAMETER = False

    SCOPE_SEPARATOR = " "
    DEFAULT_SCOPE = ["basic", "email"]

    name = "controll"

    @property
    def base_url(self) -> str:
        if self.setting("BASE_URL"):
            return self.setting("BASE_URL")

        raise Exception("BASE_URL not set")

    def authorization_url(self):
        return f"{self.base_url}/auth/authorize"

    def access_token_url(self):
        return f"{self.base_url}/auth/token"

    def get_user_details(self, response):
        access_token = response.get("access_token")
        if not access_token:
            return {}

        user_data = self.user_data(access_token)
        pprint(user_data)
        return {
            "email": user_data.get("oauth_user_id"),
            "perid": user_data.get("perid", user_data.get("oauth_user_id")),
        }

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(
            self.user_data_url(),
            headers={"Authorization": f"Bearer {access_token}"},
        )

    def get_user_id(self, details, response):
        return details["perid"]

    def auth_allowed(self, response, details) -> bool:
        # for now we allow all users to authenticate
        return True

    def user_data_url(self):
        return f"{self.base_url}/auth/api/user"


def controll_rights_to_wsfs(backend, details, response, *args, **kwargs):
    return {
        "can_nominate": True,
        "can_vote": True,
        "wsfs_status": True,
    }


class ControllBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        email: str | None = None,
        **kwargs: Any,
    ) -> AbstractBaseUser | None:
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if email is None:
            email = kwargs.get(UserModel.EMAIL_FIELD)

        if username is None or password is None:
            return

        try:
            user = UserModel.objects.get(Q(username=username) & Q(email=email))
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)

        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user


def create_username(perid, email):
    return f"{email}:::{perid}"
