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

from app.infrastructure.database.mysql_client import (
    test_mysql_connection,
)

from app.modules.credentials.service import (
    get_credential_by_key,
    resolve_credential_secret,
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

@router.post("/{source_id}/test-connection")
def test_data_source_connection(
    source_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    测试数据源真实连接。

    当前版本首先支持 MySQL。
    """

    # 1. 权限判断
    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="datasource:test_connection",
        action="TEST_CONNECTION",
    )

    # 2. 查询数据源
    source = get_source_by_id(
        db,
        source_id,
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="数据源不存在",
        )

    # 3. 检查数据源状态
    if source.status != "active":
        raise HTTPException(
            status_code=400,
            detail="数据源当前未启用",
        )

    # 4. 当前只支持 MySQL
    if source.source_type != "mysql":
        raise HTTPException(
            status_code=400,
            detail="当前连接测试仅支持MySQL数据源",
        )

    # 5. 检查必要连接参数
    if not source.host:
        raise HTTPException(
            status_code=400,
            detail="数据源未配置host",
        )

    if not source.port:
        raise HTTPException(
            status_code=400,
            detail="数据源未配置port",
        )

    if not source.database_name:
        raise HTTPException(
            status_code=400,
            detail="数据源未配置database_name",
        )

    # 6. 检查凭据引用
    if not source.secret_ref:
        raise HTTPException(
            status_code=400,
            detail="数据源尚未绑定访问凭据",
        )

    # 7. 获取凭据
    credential = get_credential_by_key(
        db,
        source.secret_ref,
    )

    if credential is None:
        raise HTTPException(
            status_code=404,
            detail="数据源绑定的凭据不存在",
        )

    # 8. 获取用户名
    username = (
        credential.username
        or source.username
    )

    if not username:
        raise HTTPException(
            status_code=400,
            detail="未配置数据库用户名",
        )

    # 9. 在内存中解密密码
    try:
        password = resolve_credential_secret(
            credential
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    # 10. 真实连接 MySQL
    result = test_mysql_connection(
        host=source.host,
        port=source.port,
        database_name=source.database_name,
        username=username,
        password=password,
    )

    # 明文密码后续不再使用
    del password

    # 11. 写审计日志
    write_audit(
        db=db,
        request=request,
        user=user,
        action="TEST_CONNECTION",
        resource="datasource:test_connection",
        result=(
            "ALLOW"
            if result["success"]
            else "FAILED"
        ),
        policy_id=decision.policy_id,
        object_count=1,
    )

    # 12. 连接失败
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    # 13. 成功返回
    return success(
        request,
        {
            "source_id": source.id,
            "source_code": source.source_code,
            "source_name": source.source_name,
            "host": source.host,
            "port": source.port,
            "database": result["database"],
            "server_version": result[
                "server_version"
            ],
            "connection_status": "connected",
        },
        message="数据源连接测试成功",
    )