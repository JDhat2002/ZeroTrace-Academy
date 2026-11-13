MEMBERSHIP_RANK = {"free": 0, "core": 1, "pro": 2, "elite": 3}


def has_membership(user, required):
    if not user.is_authenticated:
        return False
    return MEMBERSHIP_RANK.get(user.membership, 0) >= MEMBERSHIP_RANK[required]


def is_instructor(user):
    return user.is_authenticated and user.role in {"instructor", "admin"}


def is_platform_admin(user):
    return user.is_authenticated and (user.role == "admin" or user.is_staff or user.is_superuser)
