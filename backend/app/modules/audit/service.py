from uuid import uuid4

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.models import User, AuditEvent


def write_audit(
    db: Session,
    request: Request,
    user: User,
    action: str,
    resource: str,
    result: str,
    policy_id: int | None = None,
    object_count: int = 0
) -> AuditEvent:

    event = AuditEvent(
        event_id=str(uuid4()),
        request_id=request.state.request_id,
        trace_id=request.state.request_id,
        user_id=user.id,
        action=action,
        resource=resource,
        result=result,
        policy_id=policy_id,
        object_count=object_count
    )

    db.add(event)
    db.commit()

    return event