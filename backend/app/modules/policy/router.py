from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.responses import success
from app.db.session import get_db
from app.db.models import User, PolicyRule

from app.modules.policy.engine import evaluate_policy
from app.modules.audit.service import write_audit


router = APIRouter(
    prefix="/api/v1/policies",
    tags=["Policies"]
)


@router.get("")
def list_policies(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    decision = evaluate_policy(
        db, user, "policy:list"
    )

    if not decision.allowed:
        write_audit(
            db, request, user,
            "READ", "policy:list", "DENY",
            decision.policy_id
        )

        raise HTTPException(
            status_code=403,
            detail="没有查看策略的权限"
        )

    rules = db.scalars(
        select(PolicyRule)
        .order_by(
            PolicyRule.priority.desc(),
            PolicyRule.id.asc()
        )
    ).all()

    write_audit(
        db, request, user,
        "READ", "policy:list", "ALLOW",
        decision.policy_id,
        object_count=len(rules)
    )

    items = [
        {
            "id": rule.id,
            "name": rule.name,
            "resource": rule.resource,
            "allowed_roles": rule.allowed_roles,
            "effect": rule.effect,
            "mask_fields": rule.mask_fields,
            "priority": rule.priority,
            "enabled": rule.enabled
        }
        for rule in rules
    ]

    return success(
        request,
        {"items": items}
    )