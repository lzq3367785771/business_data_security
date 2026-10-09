from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.responses import success
from app.db.session import get_db
from app.db.models import User, Customer

from app.modules.policy.engine import evaluate_policy
from app.modules.masking.service import present_customer
from app.modules.audit.service import write_audit


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Customers Demo"]
)


@router.get("")
def list_customers(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    decision = evaluate_policy(
        db,
        user,
        "customer:list"
    )

    if not decision.allowed:
        write_audit(
            db, request, user,
            "READ", "customer:list", "DENY",
            decision.policy_id
        )

        raise HTTPException(
            status_code=403,
            detail="没有访问客户数据的权限"
        )

    customers = db.scalars(
        select(Customer)
        .order_by(Customer.id)
        .limit(limit)
    ).all()

    items = [
        present_customer(
            customer,
            decision.mask_fields
        )
        for customer in customers
    ]

    write_audit(
        db, request, user,
        "READ", "customer:list", "ALLOW",
        decision.policy_id,
        object_count=len(items)
    )

    return success(
        request,
        {
            "items": items,
            "total_returned": len(items),
            "mask_fields": list(
                decision.mask_fields
            )
        }
    )