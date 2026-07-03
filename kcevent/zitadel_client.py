import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ZITADEL_SETTINGS_KEY = "ZITADEL"


def _get_config() -> dict:
    return getattr(settings, ZITADEL_SETTINGS_KEY, {})


def _get_access_token() -> str | None:
    """Obtain a service-account access token via client credentials flow."""
    cfg = _get_config()
    issuer = cfg.get("ISSUER_URL", "").rstrip("/")
    client_id = cfg.get("CLIENT_ID")
    client_secret = cfg.get("CLIENT_SECRET")
    if not all([issuer, client_id, client_secret]):
        logger.warning("Zitadel credentials not configured – skipping API call.")
        return None

    token_url = f"{issuer}/oauth/v2/token"
    try:
        resp = requests.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "scope": "openid urn:zitadel:iam:org:project:id:zitadel:aud",
            },
            auth=(client_id, client_secret),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except requests.RequestException as e:
        logger.error("Zitadel token fetch failed: %s", e)
        return None


def _api_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_user(
    email: str,
    first_name: str,
    last_name: str,
    phone: str = "",
) -> tuple[str | None, str | None]:
    """
    Create a human user in Zitadel and return (user_id, invitation_url).
    Returns (None, None) if not configured or on error.
    """
    cfg = _get_config()
    issuer = cfg.get("ISSUER_URL", "").rstrip("/")
    project_id = cfg.get("PROJECT_ID")
    org_id = cfg.get("ORG_ID", "")

    token = _get_access_token()
    if not token:
        return None, None

    headers = _api_headers(token)
    if org_id:
        headers["x-zitadel-orgid"] = org_id

    user_payload: dict = {
        "userName": email,
        "profile": {
            "firstName": first_name,
            "lastName": last_name,
            "displayName": f"{first_name} {last_name}",
        },
        "email": {
            "email": email,
            "isVerified": False,
        },
    }
    if phone:
        user_payload["phone"] = {"phone": phone, "isVerified": False}

    try:
        resp = requests.post(
            f"{issuer}/v2/users/human",
            json=user_payload,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        user_id = data.get("userId")
    except requests.RequestException as e:
        logger.error("Zitadel create_user failed for %s: %s", email, e)
        return None, None

    invitation_url = _create_invitation_link(user_id, issuer, project_id, headers)
    return user_id, invitation_url


def _create_invitation_link(
    user_id: str, issuer: str, project_id: str | None, headers: dict
) -> str | None:
    """Request an invitation link (redirect) for the given user."""
    payload: dict = {
        "userId": user_id,
        "expirationDuration": "604800s",
    }
    if project_id:
        payload["applicationId"] = project_id

    try:
        resp = requests.post(
            f"{issuer}/v2/users/{user_id}/invite_code",
            json=payload,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("inviteLink") or data.get("authorizationUrl")
    except requests.RequestException as e:
        logger.error("Zitadel invitation link failed for user %s: %s", user_id, e)
        return None


def get_or_create_role(role_name: str) -> bool:
    """
    Ensure the role exists in the Zitadel project.
    Returns True on success.
    """
    cfg = _get_config()
    issuer = cfg.get("ISSUER_URL", "").rstrip("/")
    project_id = cfg.get("PROJECT_ID")
    if not project_id:
        logger.warning("Zitadel PROJECT_ID not set – cannot create role.")
        return False

    token = _get_access_token()
    if not token:
        return False

    headers = _api_headers(token)
    org_id = cfg.get("ORG_ID", "")
    if org_id:
        headers["x-zitadel-orgid"] = org_id

    role_url = f"{issuer}/management/v1/projects/{project_id}/roles"
    try:
        resp = requests.post(
            role_url,
            json={"roleKey": role_name, "displayName": role_name},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 409:
            return True
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("Zitadel get_or_create_role failed for %s: %s", role_name, e)
        return False


def add_user_role(user_id: str, role_name: str) -> str | None:
    """
    Grant a project role to the user. Returns the grant ID or None.
    """
    cfg = _get_config()
    issuer = cfg.get("ISSUER_URL", "").rstrip("/")
    project_id = cfg.get("PROJECT_ID")
    org_id = cfg.get("ORG_ID", "")
    if not project_id or not user_id:
        return None

    token = _get_access_token()
    if not token:
        return None

    headers = _api_headers(token)
    if org_id:
        headers["x-zitadel-orgid"] = org_id

    grant_url = f"{issuer}/management/v1/users/{user_id}/grants"
    try:
        resp = requests.post(
            grant_url,
            json={
                "projectId": project_id,
                "roleKeys": [role_name],
            },
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("userGrantId")
    except requests.RequestException as e:
        logger.error(
            "Zitadel add_user_role failed for user %s role %s: %s",
            user_id, role_name, e
        )
        return None


def find_user_by_email(email: str) -> str | None:
    """Look up an existing Zitadel user by email and return their user_id or None."""
    cfg = _get_config()
    issuer = cfg.get("ISSUER_URL", "").rstrip("/")
    org_id = cfg.get("ORG_ID", "")

    token = _get_access_token()
    if not token:
        return None

    headers = _api_headers(token)
    if org_id:
        headers["x-zitadel-orgid"] = org_id

    try:
        resp = requests.post(
            f"{issuer}/v2/users",
            json={"queries": [{"emailQuery": {"emailAddress": email, "method": "TEXT_QUERY_METHOD_EQUALS"}}]},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json().get("result", [])
        if result:
            return result[0].get("userId")
    except requests.RequestException as e:
        logger.error("Zitadel find_user_by_email failed for %s: %s", email, e)
    return None
