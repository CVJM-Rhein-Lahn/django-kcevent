import logging
from django.contrib.auth.models import Group
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_updated, social_account_added

logger = logging.getLogger(__name__)


def _extract_oidc_roles(extra_data: dict) -> set[str]:
    """Extract Zitadel roles/groups from the OIDC social account extra_data.

    Zitadel may expose roles as either:
      - a list of group names under the "groups" claim
      - a nested dict under "urn:zitadel:iam:org:project:roles"
    """
    roles = set()

    groups = extra_data.get("groups")
    if isinstance(groups, list):
        roles.update(str(g) for g in groups)

    zitadel_roles = extra_data.get("urn:zitadel:iam:org:project:roles")
    if isinstance(zitadel_roles, dict):
        for project_key, project_roles in zitadel_roles.items():
            if isinstance(project_roles, dict):
                roles.update(str(r) for r in project_roles.keys())

    return roles


def _sync_groups(user, extra_data: dict):
    roles = _extract_oidc_roles(extra_data)

    for role_name in roles:
        group, _ = Group.objects.get_or_create(name=role_name)
        user.groups.add(group)

    if "kcadmin" in roles:
        user.is_staff = True
        user.is_superuser = True
        user.save()


def _sync_user_from_social_account(sociallogin):
    user = sociallogin.user
    extra_data = sociallogin.account.extra_data
    if not extra_data:
        logger.warning("No extra_data available for social login of %s", user)
        return
    _sync_groups(user, extra_data)


@receiver(social_account_added)
def on_social_account_added(request, sociallogin, **kwargs):
    _sync_user_from_social_account(sociallogin)


@receiver(social_account_updated)
def on_social_account_updated(request, sociallogin, **kwargs):
    _sync_user_from_social_account(sociallogin)
