from user_agents import parse
import requests


def parse_user_agent(user_agent: str | None) -> dict:
    if not user_agent:
        return {
            "device": None,
            "browser": None,
            "os": None,
        }

    ua = parse(user_agent)

    if ua.is_mobile:
        device = "mobile"
    elif ua.is_tablet:
        device = "tablet"
    elif ua.is_pc:
        device = "desktop"
    else:
        device = "other"

    browser = ua.browser.family or None
    os = ua.os.family or None

    return {
        "device": device,
        "browser": browser,
        "os": os,
    }


def get_country_from_ip(
    ip_address: str | None,
) -> str | None:
    if not ip_address:
        return None

    try:
        response = requests.get(
            f"https://ipapi.co/{ip_address}/country/",
            timeout=2,
        )

        if response.status_code != 200:
            return None

        country = response.text.strip().upper()

        if len(country) != 2:
            return None

        return country

    except requests.RequestException:
        return None