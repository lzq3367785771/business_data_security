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
from app.db.models import User, AuditEvent
from app.modules.policy.engine import evaluate_policy
from app.modules.audit.service import write_audit


router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit"]
)


@router.get("/events")
def list_audit_events(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    decision = evaluate_policy(
        db, user, "audit:list"
    )

    if not decision.allowed:
        write_audit(
            db, request, user,
            "READ", "audit:list", "DENY",
            decision.policy_id
        )

        raise HTTPException(
            status_code=403,
            detail="没有查看审计日志的权限"
        )

    write_audit(
        db, request, user,
        "READ", "audit:list", "ALLOW",
        decision.policy_id
    )

    statement = (
        select(AuditEvent)
        .order_by(
            AuditEvent.created_at.desc(),
            AuditEvent.event_id.desc()
        )
        .limit(100)
    )

    events = db.scalars(statement).all()

    items = [
        {
            "event_id": event.event_id,
            "request_id": event.request_id,
            "trace_id": event.trace_id,
            "user_id": event.user_id,
            "action": event.action,
            "resource": event.resource,
            "result": event.result,
            "policy_id": event.policy_id,
            "object_count": event.object_count,
            "created_at": event.created_at.isoformat()
        }
        for event in events
    ]

    return success(
        request,
        {"items": items}
    )