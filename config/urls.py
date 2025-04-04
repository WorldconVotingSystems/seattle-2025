"""
URL configuration for Seattle Worldcon 2025 project.

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
1. Add an import:  from my_app import views
2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
1. Add an import:  from other_app.views import Home
2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
1. Import the include() function: from django.urls import include, path
2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import djp
import nomnom.base.views
from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import include, path
from django_svcs.apps import svcs_from
from nomnom.convention import ConventionConfiguration

convention_configuration = svcs_from().get(ConventionConfiguration)

urlpatterns = (
    [
        path("", nomnom.base.views.index, name="index"),
        path("e/", include("nomnom.nominate.urls", namespace="election")),
        path("e/", include("nomnom.canonicalize.urls", namespace="canonicalize")),
        path("convention/", include("seattle_2025_app.urls", namespace="convention")),
        path("admin/action-forms/", include("django_admin_action_forms.urls")),
        path("admin/", admin.site.urls),
        path("", include("social_django.urls", namespace="social")),
        path("accounts/", include("django.contrib.auth.urls")),
        path("watchman/", include("watchman.urls")),
        path("__reload__/", include("django_browser_reload.urls")),
        path("", include("seattle_2025_app.urls", namespace="seattle_2025_app")),
    ]
    + debug_toolbar_urls()
    + djp.urlpatterns()
)

if convention_configuration.hugo_packet_backend is not None:
    urlpatterns.append(
        path("p/", include("nomnom.hugopacket.urls", namespace="hugopacket")),
    )

if convention_configuration.advisory_votes_enabled:
    urlpatterns.append(path("bm/", include("nomnom.advise.urls", namespace="advise")))

handler403 = "nomnom.nominate.views.access_denied"
