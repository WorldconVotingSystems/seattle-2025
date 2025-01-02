from social_core.backends.oauth import BaseOAuth2


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

    def authorization_url(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return f"{self.base_url}/auth/authorize"

    def access_token_url(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return f"{self.base_url}/auth/token"

    def user_data_url(self):
        return f"{self.base_url}/auth/api/user"
