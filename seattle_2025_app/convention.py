from datetime import datetime, timezone

from nomnom.convention import (
    ConventionConfiguration,
    ConventionTheme,
)

theme = ConventionTheme(
    stylesheets="css/seattle-2025.css",
    font_urls=[],
)

convention = ConventionConfiguration(
    name="Seattle Worldcon 2025",
    subtitle="Convention Subtitle (in seattle_2025_app/convention.py)",
    slug="seattle-2025",
    site_url="https://seattlein2025.org",
    nomination_eligibility_cutoff=datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
    hugo_help_email="hugo-help@seattlein2025.org",
    hugo_admin_email="hugo-admin@seattlein2025.org",
    hugo_packet_backend="digitalocean",
    registration_email="registration@seattlein2025.org",
    logo="images/logo_withouttitle_transparent-300x293.png",
    logo_alt_text="Seattle Worldcon 2025 logo",
    urls_app_name="seattle_2025_app",
    advisory_votes_enabled=True,
)
