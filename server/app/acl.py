from fastapi import Depends, HTTPException, status
from app.deps import get_current_user
from app.model import User
from typing import Literal


from fastapi_permissions import (
    Allow,
    Authenticated,
    Deny,
    Everyone,
    configure_permissions,
    list_permissions,
    )

valid_permissions = Literal["admin", "user"]

user_acl = ["view", "update_user", "edit"]
admin_acl = user_acl + ["view_all", "update_permission", "delete"]

def generate_acl(role, acl_list):
    return [
        (Allow, role, acl)
        for acl in acl_list
    ]

admin_acl_permission = generate_acl("admin", admin_acl)
user_acl_permission = generate_acl("user", user_acl)

all_acl_permission = admin_acl_permission + user_acl_permission

def check_acl(acl: str):
    if acl not in admin_acl:
        raise Exception(f"Invalid acl ({acl}). Valid acls are {admin_acl}")
    return acl

def check_permission(permission: str):
    permissions = valid_permissions.__args__
    if permission not in permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": f"Invalid permission ({permission}). Valid permissions are {permissions}",
                "body": f"Invalid permission ({permission}). Valid permissions are {permissions}"
            },
        )
    return permission

def get_active_principals(user: User = Depends(get_current_user)):
    if user:

        # user is logged in
        principals = [Everyone, Authenticated]
        principal = user["principal"]
        
        principals.extend([principal])

    else:
        # user is not logged in
        principals = [Everyone]
    return principals

    