import pymysql

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from sqlalchemy.orm import Session

from app.core.authorization import require_policy
from app.core.dependencies import get_current_user
from app.core.responses import success

from app.db.models import User
from app.db.session import get_db

from app.modules.audit.service import write_audit

from app.modules.assets.scanner import (
    scan_mysql_metadata,
)

from app.modules.credentials.service import (
    get_credential_by_key,
    resolve_credential_secret,
)

from app.modules.data_sources.service import (
    get_source_by_id,
)
from app.modules.assets.service import (
    sync_mysql_assets,
)
from app.modules.assets.service import (
    get_asset_tree,
)


router = APIRouter(
    prefix="/api/v1/data-sources",
    tags=["Asset Discovery"],
)


@router.post("/{source_id}/scan")
def scan_data_source(
    source_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    扫描数据源元数据。

    当前版本：
    - 支持 MySQL
    - 扫描数据库表
    - 扫描字段结构
    - 不读取具体业务数据内容
    - 暂不写入资产目录表
    """

    # -------------------------
    # 1. 权限判断
    # -------------------------

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="datasource:scan_metadata",
        action="SCAN_METADATA",
    )

    # -------------------------
    # 2. 查询数据源
    # -------------------------

    source = get_source_by_id(
        db,
        source_id,
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="数据源不存在",
        )

    # -------------------------
    # 3. 数据源状态
    # -------------------------

    if source.status != "active":
        raise HTTPException(
            status_code=400,
            detail="数据源当前未启用",
        )

    # -------------------------
    # 4. 当前只支持 MySQL
    # -------------------------

    if source.source_type != "mysql":
        raise HTTPException(
            status_code=400,
            detail="当前元数据扫描仅支持MySQL数据源",
        )

    # -------------------------
    # 5. 检查连接信息
    # -------------------------

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

    if not source.secret_ref:
        raise HTTPException(
            status_code=400,
            detail="数据源尚未绑定访问凭据",
        )

    # -------------------------
    # 6. 获取凭据
    # -------------------------

    credential = get_credential_by_key(
        db,
        source.secret_ref,
    )

    if credential is None:
        raise HTTPException(
            status_code=404,
            detail="数据源绑定的凭据不存在",
        )

    username = (
        credential.username
        or source.username
    )

    if not username:
        raise HTTPException(
            status_code=400,
            detail="未配置数据库用户名",
        )

    # -------------------------
    # 7. 解密密码
    # -------------------------

    try:
        password = resolve_credential_secret(
            credential
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    # -------------------------
    # 8. 执行元数据扫描
    # -------------------------

    try:
        scan_result = scan_mysql_metadata(
            host=source.host,
            port=source.port,
            database_name=source.database_name,
            username=username,
            password=password,
        )

    except pymysql.MySQLError as exc:

        write_audit(
            db=db,
            request=request,
            user=user,
            action="SCAN_METADATA",
            resource="datasource:scan_metadata",
            result="FAILED",
            policy_id=decision.policy_id,
            object_count=0,
        )

        raise HTTPException(
            status_code=400,
            detail=f"MySQL元数据扫描失败：{exc}",
        ) from exc

    finally:
        # 后续不再使用明文密码
        if "password" in locals():
            del password

    # -------------------------
    # 9. 审计
    # -------------------------

    write_audit(
        db=db,
        request=request,
        user=user,
        action="SCAN_METADATA",
        resource="datasource:scan_metadata",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=scan_result[
            "column_count"
        ],
    )

    # -------------------------
    # 10. 返回扫描结果
    # -------------------------

    return success(
        request,
        {
            "source_id":
                source.id,

            "source_code":
                source.source_code,

            "source_name":
                source.source_name,

            "database_name":
                scan_result[
                    "database_name"
                ],

            "table_count":
                scan_result[
                    "table_count"
                ],

            "column_count":
                scan_result[
                    "column_count"
                ],

            "tables":
                scan_result[
                    "tables"
                ],
        },
        message="数据源元数据扫描成功",
    )

@router.post("/{source_id}/sync-assets")
def sync_data_source_assets(
    source_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    扫描数据源并同步到本地资产目录。
    """

    # -------------------------
    # 1. 权限
    # -------------------------

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="datasource:sync_assets",
        action="SYNC_ASSETS",
    )

    # -------------------------
    # 2. 查询数据源
    # -------------------------

    source = get_source_by_id(
        db,
        source_id,
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="数据源不存在",
        )

    if source.status != "active":
        raise HTTPException(
            status_code=400,
            detail="数据源当前未启用",
        )

    if source.source_type != "mysql":
        raise HTTPException(
            status_code=400,
            detail="当前资产同步仅支持MySQL数据源",
        )

    if (
        not source.host
        or not source.port
        or not source.database_name
    ):
        raise HTTPException(
            status_code=400,
            detail="MySQL数据源连接参数不完整",
        )

    if not source.secret_ref:
        raise HTTPException(
            status_code=400,
            detail="数据源尚未绑定访问凭据",
        )

    # -------------------------
    # 3. 凭据
    # -------------------------

    credential = get_credential_by_key(
        db,
        source.secret_ref,
    )

    if credential is None:
        raise HTTPException(
            status_code=404,
            detail="数据源绑定的凭据不存在",
        )

    username = (
        credential.username
        or source.username
    )

    if not username:
        raise HTTPException(
            status_code=400,
            detail="未配置数据库用户名",
        )

    try:
        password = resolve_credential_secret(
            credential
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    # -------------------------
    # 4. 扫描外部数据库
    # -------------------------

    try:
        scan_result = scan_mysql_metadata(
            host=source.host,
            port=source.port,
            database_name=
                source.database_name,
            username=username,
            password=password,
        )

    except pymysql.MySQLError as exc:

        write_audit(
            db=db,
            request=request,
            user=user,
            action="SYNC_ASSETS",
            resource=
                "datasource:sync_assets",
            result="FAILED",
            policy_id=decision.policy_id,
            object_count=0,
        )

        raise HTTPException(
            status_code=400,
            detail=f"MySQL资产扫描失败：{exc}",
        ) from exc

    finally:
        if "password" in locals():
            del password

    # -------------------------
    # 5. 保存到资产目录
    # -------------------------

    try:
        sync_result = sync_mysql_assets(
            db=db,
            source_id=source.id,
            scan_result=scan_result,
        )

    except Exception:
        db.rollback()
        raise

    # -------------------------
    # 6. 审计
    # -------------------------

    write_audit(
        db=db,
        request=request,
        user=user,
        action="SYNC_ASSETS",
        resource="datasource:sync_assets",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=
            scan_result["column_count"],
    )

    # -------------------------
    # 7. 返回
    # -------------------------

    return success(
        request,
        {
            "source_id":
                source.id,

            "source_code":
                source.source_code,

            **sync_result,
        },
        message="数据资产同步成功",
    )



@router.get(
    "/{source_id}/assets"
)
def get_data_source_assets(
    source_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    查询指定数据源已经同步到平台的资产目录。
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="asset:list",
        action="LIST_ASSETS",
    )


    tree = get_asset_tree(
        db=db,
        source_id=source_id,
    )


    write_audit(
        db=db,
        request=request,
        user=user,
        action="LIST_ASSETS",
        resource="asset:list",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=tree[
            "column_count"
        ],
    )


    return success(
        request,
        tree,
        message="资产目录获取成功",
    )