from datetime import datetime, timezone

from nomnom.convention import (
    ConventionConfiguration,
    ConventionTheme,
)

theme = ConventionTheme(
    stylesheets="css/seattle-2025.css",
    font_urls=[
        "https://fonts.googleapis.com/css2?family=Bigelow+Rules&family=Cookie&display=swap",
    ],
)

convention = ConventionConfiguration(
    name="Seattle Worldcon 2025",
    subtitle="Building Yesterday’s Future–For Everyone",
    slug="seattle-2025",
    site_url="https://seattlein2025.org",
    nomination_eligibility_cutoff=datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
    hugo_help_email="hugo-help@seattlein2025.org",
    hugo_admin_email="hugo-admin@seattlein2025.org",
    hugo_packet_backend="digitalocean",
    registration_email="registration@seattlein2025.org",
    logo="images/seattle-worldcon-logo-small.png",
    logo_alt_text="Seattle Worldcon 2025 logo",
    urls_app_name="seattle_2025_app",
    advisory_votes_enabled=True,
)
