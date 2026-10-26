import pymysql

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

from app.core.responses import (
    success,
)

from app.db.models import User

from app.db.session import get_db

from app.modules.audit.service import (
    write_audit,
)

from app.modules.credentials.service import (
    get_credential_by_key,
    resolve_credential_secret,
)

from app.modules.data_sources.service import (
    get_source_by_id,
)

from app.modules.data_access.service import (
    get_confirmed_sensitive_field_levels,
    get_confirmed_sensitive_field_types,
    get_synced_table,
    read_mysql_table,
)

from app.modules.masking.service import (
    mask_rows,
)

from app.modules.systems.service import (
    get_system_by_id,
)

from app.modules.risk_control.service import (
    ACTION_ALLOW,
    ACTION_BLOCK,
    ACTION_LIMIT,
    ACTION_MASK,
    decide_data_access_control,
)



router = APIRouter(
    prefix="/api/v1/data-access",
    tags=["Business Data Access"],
)


@router.get(
    "/{source_id}/tables/{table_name}/preview"
)
def preview_business_table(
    source_id: int,
    table_name: str,
    request: Request,

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),

    db: Session = Depends(get_db),

    user: User = Depends(
        get_current_user
    ),
):
    """
    读取真实业务数据。

    当前第一阶段：
    - 仅管理员策略允许访问
    - 仅支持 MySQL
    - 只读取已经同步进资产目录的表
    - 最多返回 100 行
    - 暂不执行动态脱敏
    """

    # =========================
    # 1. 权限判断
    # =========================

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="data_access:preview",
        action="READ_BUSINESS_DATA",
    )

    # =========================
    # 2. 数据源
    # =========================

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
            detail="当前业务数据访问仅支持MySQL",
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


    system = get_system_by_id(
        db,
        source.system_id,
    )



    # =========================
    # 3. 必须是已同步资产
    # =========================

    asset = get_synced_table(
        db=db,
        source_id=source.id,
        table_name=table_name,
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "该数据表不存在，"
                "或尚未同步到平台资产目录"
            ),
        )

    database = asset["database"]
    table = asset["table"]
    columns = asset["columns"]

    if not columns:
        raise HTTPException(
            status_code=400,
            detail="该数据表没有可读取字段",
        )

    # =========================
    # 4. 获取访问凭据
    # =========================

    if not source.secret_ref:
        raise HTTPException(
            status_code=400,
            detail="数据源尚未绑定访问凭据",
        )

    credential = get_credential_by_key(
        db,
        source.secret_ref,
    )

    if credential is None:
        raise HTTPException(
            status_code=404,
            detail="数据源绑定的凭据不存在",
        )

    if credential.status != "active":
        raise HTTPException(
            status_code=400,
            detail="数据源凭据当前未启用",
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




    # =========================
    # 5. 风险处置决策
    # =========================

    risk_decision = (
        decide_data_access_control(
            db=db,
            user=user,
            source_id=source.id,
            database_name=(
                database.database_name
            ),
            table_name=(
                table.table_name
            ),
        )
    )


    risk_action = (
        risk_decision["action"]
    )

    risk_control_applied = (
        risk_decision[
            "risk_control_applied"
        ]
    )

    risk_control_reason = (
        risk_decision["reason"]
    )

    active_anomaly_id = (
        risk_decision[
            "active_anomaly_id"
        ]
    )

    max_rows = (
        risk_decision.get(
            "max_rows"
        )
    )

    mask_required = (
        risk_decision.get(
            "mask_required",
            False,
        )
    )


    # =========================
    # 6. 计算实际读取行数
    # =========================

    effective_limit = limit


    if (
        risk_action
        == ACTION_LIMIT
        and max_rows is not None
    ):

        effective_limit = min(
            limit,
            max_rows,
        )



    # =========================
    # 7. BLOCK：完全阻断
    # =========================

    if (
        risk_action
        == ACTION_BLOCK
    ):

        write_audit(
            db=db,
            request=request,
            user=user,
            action="READ_BUSINESS_DATA",
            resource="data_access:preview",
            result="DENY",
            policy_id=decision.policy_id,
            object_count=0,

            details={
                "system_id":
                    source.system_id,

                "system_code":
                    (
                        system.system_code
                        if system
                        else None
                    ),

                "source_id":
                    source.id,

                "source_code":
                    source.source_code,

                "database_name":
                    database.database_name,

                "table_name":
                    table.table_name,

                "access_mode":
                    "blocked",

                "risk_action":
                    risk_action,

                "risk_control_applied":
                    True,

                "risk_control_reason":
                    risk_control_reason,

                "active_anomaly_id":
                    active_anomaly_id,

                "requested_limit":
                    limit,

                "effective_limit":
                    0,

                "limit_applied":
                    True,

                "masked_fields":
                    [],

                "returned_rows":
                    0,
            },
        )


        raise HTTPException(
            status_code=403,
            detail={
                "message":
                    "检测到已确认的高风险异常，"
                    "本次业务数据访问已被阻断",

                "risk_action":
                    ACTION_BLOCK,

                "risk_control_reason":
                    risk_control_reason,

                "active_anomaly_id":
                    active_anomaly_id,
            },
        )



    # =========================
    # 8. 临时解密数据库密码
    # =========================

    try:
        password = (
            resolve_credential_secret(
                credential
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc




    # =========================
    # 6. 读取真实业务数据
    # =========================

    try:
        items = read_mysql_table(
            host=source.host,
            port=source.port,
            database_name=(
                database.database_name
            ),
            username=username,
            password=password,
            table_name=(
                table.table_name
            ),
            column_names=[
                column.column_name
                for column in columns
            ],
            limit=effective_limit,
        )
    except pymysql.MySQLError as exc:
        write_audit(
            db=db,
            request=request,
            user=user,
            action="READ_BUSINESS_DATA",
            resource="data_access:preview",
            result="FAILED",
            policy_id=(
                decision.policy_id
            ),
            object_count=0,

            details={
                "system_id":
                    source.system_id,

                "system_code":
                    (
                        system.system_code
                        if system
                        else None
                    ),

                "source_id":
                    source.id,

                "source_code":
                    source.source_code,

                "database_name":
                    database.database_name,

                "table_name":
                    table.table_name,

                "requested_limit":
                    limit,

                "access_mode":
                    None,

                "masked_fields":
                    [],
            },
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "读取业务数据失败："
                f"{exc}"
            ),
        ) from exc
    finally:
        if "password" in locals():
            del password

    # =========================
    # 7. 动态敏感字段脱敏
    # =========================

    sensitive_field_types = (
        get_confirmed_sensitive_field_types(
            db=db,
            table_asset_id=table.id,
        )
    )

    sensitive_field_levels = (
        get_confirmed_sensitive_field_levels(
            db=db,
            table_asset_id=table.id,
        )
    )



    # =========================
    # 9. 执行风险处置动作
    # =========================

    access_mode = "raw"
    masked_fields = []


    if (
        risk_action
        == ACTION_MASK
    ):

        items = mask_rows(
            rows=items,
            field_types=(
                sensitive_field_types
            ),
        )

        access_mode = "masked"

        masked_fields = sorted(
            sensitive_field_types.keys()
        )


    elif (
        risk_action
        == ACTION_LIMIT
    ):

        if mask_required:

            items = mask_rows(
                rows=items,
                field_types=(
                    sensitive_field_types
                ),
            )

            access_mode = (
                "limited_masked"
            )

            masked_fields = sorted(
                sensitive_field_types.keys()
            )

        else:

            access_mode = "limited"


    elif (
        risk_action
        == ACTION_ALLOW
    ):

        access_mode = "raw"


    else:

        raise HTTPException(
            status_code=500,
            detail=(
                "当前风险处置动作"
                f" {risk_action} "
                "尚未实现"
            ),
        )


    # =========================
    # 8. 审计
    # =========================

    write_audit(
        db=db,
        request=request,
        user=user,
        action="READ_BUSINESS_DATA",
        resource="data_access:preview",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=len(items),

        details={
            "system_id":
                source.system_id,

            "system_code":
                (
                    system.system_code
                    if system
                    else None
                ),

            "source_id":
                source.id,

            "source_code":
                source.source_code,

            "database_name":
                database.database_name,

            "table_name":
                table.table_name,

            "access_mode":
                access_mode,

            "sensitive_fields":
                sorted(
                    sensitive_field_types.keys()
                ),

            "sensitive_field_levels":
                sensitive_field_levels,

            "risk_control_applied":
                risk_control_applied,

            "risk_control_reason":
                risk_control_reason,

            "risk_action":
                risk_action,    

            "active_anomaly_id":
                active_anomaly_id,

            "masked_fields":
                masked_fields,

            "requested_limit":
                limit,

            "effective_limit":
                effective_limit,

            "limit_applied":
                (
                    effective_limit
                    < limit
                ),

            "returned_rows":
                len(items),
        },
    )

    # =========================
    # 9. 返回
    # =========================

    return success(
        request,
        {
            "source_id": source.id,
            "source_code": source.source_code,
            "source_name": source.source_name,
            "database_name": database.database_name,
            "table_name": table.table_name,
            "access_mode": access_mode,
            "masked_fields": masked_fields,

            "risk_action":
                risk_action,

            "risk_control_applied":
                risk_control_applied,

            "risk_control_reason":
                risk_control_reason,

            "active_anomaly_id":
                active_anomaly_id,
                        

            "requested_limit":
                limit,

            "effective_limit":
                effective_limit,

            "limit_applied":
                (
                    effective_limit
                    < limit
                ),


            "columns": [
                {
                    "column_asset_id": column.id,
                    "column_name": column.column_name,
                    "data_type": column.data_type,
                }
                for column in columns
            ],
            "items": items,
            "total_returned": len(items),
            "limit": limit,
        },
        message="真实业务数据读取成功",
    )