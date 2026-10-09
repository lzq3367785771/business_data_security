from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)

from sqlalchemy.orm import Session

from app.core.authorization import (
    require_policy,
)

from app.core.dependencies import (
    get_current_user,
)

from app.core.responses import success

from app.db.models import User

from app.db.session import get_db

from app.modules.audit.service import (
    write_audit,
)

from app.modules.data_sources.schemas import (
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceStatusUpdate,
)

from app.modules.data_sources.service import (
    create_source,
    get_source_by_code,
    get_source_by_id,
    list_sources,
    serialize_source,
    system_exists,
    update_source,
    update_source_status,
)


router = APIRouter(
    prefix="/api/v1/data-sources",
    tags=["Data Sources"],
)


@router.get("")
def get_data_sources(
    request: Request,

    system_id: int | None = Query(
        default=None,
        gt=0,
    ),

    db: Session = Depends(get_db),

    user: User = Depends(
        get_current_user
    ),
):

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="datasource:list",
        action="READ",
    )

    sources = list_sources(
        db,
        system_id,
    )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="READ",
        resource="datasource:list",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=len(sources),
    )

    return success(
        request,
        {
            "items": [
                serialize_source(source)
                for source in sources
            ],
            "total": len(sources),
        },
    )


@router.get("/{source_id}")
def get_data_source(
    source_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="datasource:detail",
        action="READ",
    )

    source = get_source_by_id(
        db,
        source_id,
    )

    if source is None:

        raise HTTPException(
            status_code=404,
            detail="数据源不存在",
        )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="READ",
        resource="datasource:detail",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        serialize_source(source),
    )


@router.post("")
def create_data_source(
    payload: DataSourceCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="datasource:create",
        action="CREATE",
    )

    if not system_exists(
        db,
        payload.system_id,
    ):

        raise HTTPException(
            status_code=404,
            detail="所属业务系统不存在",
        )

    normalized_code = (
        payload.source_code
        .strip()
        .upper()
    )

    exists = get_source_by_code(
        db,
        payload.system_id,
        normalized_code,
    )

    if exists is not None:

        raise HTTPException(
            status_code=409,
            detail="该业务系统下的数据源编码已存在",
        )

    source = create_source(
        db,
        payload,
    )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="CREATE",
        resource="datasource:create",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        serialize_source(source),
        message="数据源创建成功",
    )


@router.put("/{source_id}")
def modify_data_source(
    source_id: int,
    payload: DataSourceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="datasource:update",
        action="UPDATE",
    )

    source = get_source_by_id(
        db,
        source_id,
    )

    if source is None:

        raise HTTPException(
            status_code=404,
            detail="数据源不存在",
        )

    source = update_source(
        db,
        source,
        payload,
    )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="UPDATE",
        resource="datasource:update",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        serialize_source(source),
        message="数据源修改成功",
    )


@router.patch("/{source_id}/status")
def change_data_source_status(
    source_id: int,
    payload: DataSourceStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="datasource:status",
        action="UPDATE",
    )

    source = get_source_by_id(
        db,
        source_id,
    )

    if source is None:

        raise HTTPException(
            status_code=404,
            detail="数据源不存在",
        )

    source = update_source_status(
        db,
        source,
        payload.status,
    )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="UPDATE",
        resource="datasource:status",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        serialize_source(source),
        message="数据源状态修改成功",
    )