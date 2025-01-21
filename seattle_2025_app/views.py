from django.http import HttpRequest, HttpResponse


def controll_redirect(request: HttpRequest) -> HttpResponse:
    return HttpResponse(
        b"Hello, world. You're at the Seattle 2025 app controll redirect."
    )
