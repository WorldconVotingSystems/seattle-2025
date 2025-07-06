import jwt
import sentry_sdk
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .auth import create_member


@transaction.atomic
def controll_redirect(request: HttpRequest) -> HttpResponse:
    # only allow GET methods
    if request.method != "GET":
        return HttpResponse(status=405)

    token = request.GET.get("r")

    if token is None or isinstance(token, list):
        return render(
            request,
            "registration/controll_login_failed.html",
            context={
                "reason": "No token or malformed token provided. Please try again."
            },
            status=403,
        )

    user = authenticate(token=token)
    if user is not None:
        login(request, user)
        return redirect("/")

    # okay, the user couldn't be authenticated directly. Now we check the token
    # ourselves and see if we can _create_ a member from it.
    try:
        payload = jwt.decode(
            token,
            settings.CONTROLL_JWT_KEY,
            algorithms=["HS256", "HS512"],
        )
    except jwt.InvalidTokenError as e:
        sentry_sdk.capture_exception(e)

        return render(
            request,
            "registration/controll_login_failed.html",
            context={"reason": "Invalid token. Please try again."},
            status=403,
        )

    if (member := create_member(request, payload)) is not None:
        login(request, member.user, backend="seattle_2025_app.auth.ControllBackend")
        return redirect("/")

    # TODO: we should probably explain why we're not letting them in

    return HttpResponse(status=403)
