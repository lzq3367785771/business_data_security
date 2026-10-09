from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.db.models import User
from app.modules.audit.service import write_audit
from app.modules.policy.engine import evaluate_policy


def require_policy(
    db: Session,
    request: Request,
    user: User,
    resource: str,
    action: str,
):
    """
    统一权限检查。

    所有业务模块后续统一调用这里，
    避免重复编写权限判断逻辑。
    """

    decision = evaluate_policy(
        db,
        user,
        resource,
    )

    if not decision.allowed:

        write_audit(
            db=db,
            request=request,
            user=user,
            action=action,
            resource=resource,
            result="DENY",
            policy_id=decision.policy_id,
        )

        raise HTTPException(
            status_code=403,
            detail="没有执行该操作的权限",
        )

    return decision