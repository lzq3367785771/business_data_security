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
    resolve_credential_secret,
)

from app.modules.data_sources.service import (
    get_source_by_id,
)

from app.modules.data_access.service import (
    build_data_access_execution_plan,
    get_confirmed_sensitive_field_levels,
    get_confirmed_sensitive_field_types,
    prepare_data_access_asset,
    prepare_data_access_credential,
    read_mysql_table,
    apply_data_access_action,
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

    当前能力：
    - 仅支持 MySQL 数据源
    - 只读取已经同步进资产目录的表
    - 单次请求最多返回 100 行
    - 根据访问策略和风险状态执行 ALLOW / MASK / LIMIT / BLOCK
    - 对敏感字段执行动态脱敏
    - 记录数据访问及风险控制审计日志
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




    system = get_system_by_id(
        db,
        source.system_id,
    )


    # =========================
    # 3. 数据访问资产上下文
    # =========================

    try:

        asset = prepare_data_access_asset(
            db=db,
            source=source,
            table_name=table_name,
        )

    except LookupError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


    database = asset["database"]
    table = asset["table"]
    columns = asset["columns"]



    # =========================
    # 4. 准备访问凭据
    # =========================

    try:

        credential_context = (
            prepare_data_access_credential(
                db=db,
                source=source,
            )
        )

    except LookupError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


    credential = (
        credential_context[
            "credential"
        ]
    )

    username = (
        credential_context[
            "username"
        ]
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


    # =========================
    # 5. 风险执行计划
    # =========================

    execution_plan = (
        build_data_access_execution_plan(
            risk_decision=risk_decision,
            requested_limit=limit,
        )
    )


    risk_action = (
        execution_plan[
            "risk_action"
        ]
    )

    risk_control_applied = (
        execution_plan[
            "risk_control_applied"
        ]
    )

    risk_control_reason = (
        execution_plan[
            "risk_control_reason"
        ]
    )

    active_anomaly_id = (
        execution_plan[
            "active_anomaly_id"
        ]
    )

    mask_required = (
        execution_plan[
            "mask_required"
        ]
    )

    effective_limit = (
        execution_plan[
            "effective_limit"
        ]
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
    # 执行读取后的风险动作
    # =========================

    try:

        action_result = (
            apply_data_access_action(
                items=items,
                risk_action=risk_action,
                mask_required=mask_required,
                sensitive_field_types=(
                    sensitive_field_types
                ),
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


    items = (
        action_result["items"]
    )

    access_mode = (
        action_result[
            "access_mode"
        ]
    )

    masked_fields = (
        action_result[
            "masked_fields"
        ]
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