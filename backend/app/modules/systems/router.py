from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
)

from app.core.responses import success

from app.db.models import User

from app.db.session import get_db

from app.modules.audit.service import (
    write_audit,
)

from app.modules.policy.engine import (
    evaluate_policy,
)

from app.modules.systems.schemas import (
    BusinessSystemCreate,
    BusinessSystemUpdate,
    BusinessSystemStatusUpdate,
)

from app.modules.systems.service import (
    create_system,
    get_system_by_code,
    get_system_by_id,
    list_systems,
    serialize_system,
    update_system,
    update_system_status,
)

from app.core.authorization import require_policy




router = APIRouter(
    prefix="/api/v1/systems",
    tags=["Business Systems"],
)





@router.get("")
def get_business_systems(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    查询业务系统列表
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="system:list",
        action="READ",
    )

    systems = list_systems(db)

    write_audit(
        db=db,
        request=request,
        user=user,
        action="READ",
        resource="system:list",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=len(systems),
    )

    return success(
        request,
        {
            "items": [
                serialize_system(system)
                for system in systems
            ],
            "total": len(systems),
        },
    )


@router.get("/{system_id}")
def get_business_system(
    system_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    查询单个业务系统
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="system:detail",
        action="READ",
    )

    system = get_system_by_id(
        db,
        system_id,
    )

    if system is None:
        raise HTTPException(
            status_code=404,
            detail="业务系统不存在",
        )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="READ",
        resource="system:detail",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        serialize_system(system),
    )


@router.post("")
def create_business_system(
    payload: BusinessSystemCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    新增业务系统
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="system:create",
        action="CREATE",
    )

    normalized_code = (
        payload.system_code.strip().upper()
    )

    exists = get_system_by_code(
        db,
        normalized_code,
    )

    if exists is not None:
        raise HTTPException(
            status_code=409,
            detail="系统编码已经存在",
        )

    system = create_system(
        db,
        payload,
    )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="CREATE",
        resource="system:create",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        serialize_system(system),
        message="业务系统创建成功",
    )


@router.put("/{system_id}")
def modify_business_system(
    system_id: int,
    payload: BusinessSystemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    修改业务系统
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="system:update",
        action="UPDATE",
    )

    system = get_system_by_id(
        db,
        system_id,
    )

    if system is None:
        raise HTTPException(
            status_code=404,
            detail="业务系统不存在",
        )

    system = update_system(
        db,
        system,
        payload,
    )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="UPDATE",
        resource="system:update",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        serialize_system(system),
        message="业务系统修改成功",
    )


@router.patch("/{system_id}/status")
def change_business_system_status(
    system_id: int,
    payload: BusinessSystemStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    启用 / 停用业务系统
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="system:status",
        action="UPDATE",
    )

    system = get_system_by_id(
        db,
        system_id,
    )

    if system is None:
        raise HTTPException(
            status_code=404,
            detail="业务系统不存在",
        )

    system = update_system_status(
        db,
        system,
        payload.status,
    )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="UPDATE",
        resource="system:status",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        serialize_system(system),
        message="系统状态修改成功",
    )