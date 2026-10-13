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

from app.core.responses import success

from app.db.models import User
from app.db.session import get_db

from app.modules.audit.service import (
    write_audit,
)

from app.modules.sensitive_detection.service import (
    detect_sensitive_columns,
)

from app.modules.credentials.service import (
    get_credential_by_key,
    resolve_credential_secret,
)

from app.modules.data_sources.service import (
    get_source_by_id,
)

from app.modules.sensitive_detection.schemas import (
    SensitiveFieldReviewRequest,
)

from app.modules.sensitive_detection.service import (
    detect_sensitive_columns,
    detect_sensitive_columns_with_content,
    list_sensitive_field_profiles,
    review_sensitive_field,
)



router = APIRouter(
    prefix="/api/v1/sensitive-fields",
    tags=["Sensitive Detection"],
)


@router.post("/detect")
def detect_sensitive_fields(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    对当前资产目录中的 active 字段
    执行第一阶段敏感字段识别。

    当前识别依据：
    - 字段名称规则

    后续将增加：
    - 数据内容抽样
    - 正则匹配
    - AI语义识别
    - 人工复核
    """

    # -------------------------
    # 1. 权限判断
    # -------------------------

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="sensitive:detect",
        action="DETECT_SENSITIVE",
    )

    # -------------------------
    # 2. 执行识别
    # -------------------------

    result = detect_sensitive_columns(
        db=db,
    )

    # -------------------------
    # 3. 审计
    # -------------------------

    write_audit(
        db=db,
        request=request,
        user=user,
        action="DETECT_SENSITIVE",
        resource="sensitive:detect",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=result[
            "total_columns"
        ],
    )

    # -------------------------
    # 4. 返回
    # -------------------------

    return success(
        request,
        result,
        message="敏感字段识别完成",
    )


@router.post("/detect-content/{source_id}")
def detect_sensitive_fields_by_content(
    source_id: int,
    request: Request,
    sample_limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    基于字段名 + 真实数据抽样
    执行敏感字段融合识别。

    原始业务数据：
    - 不返回前端
    - 不写入本地数据库
    - 不写入审计日志
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="sensitive:content_detect",
        action="CONTENT_DETECT",
    )

    # -------------------------
    # 数据源
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
            detail="当前仅支持MySQL内容识别",
        )

    if (
        not source.host
        or not source.port
        or not source.database_name
    ):
        raise HTTPException(
            status_code=400,
            detail="MySQL连接参数不完整",
        )

    if not source.secret_ref:
        raise HTTPException(
            status_code=400,
            detail="数据源尚未绑定凭据",
        )

    # -------------------------
    # 凭据
    # -------------------------

    credential = get_credential_by_key(
        db,
        source.secret_ref,
    )

    if credential is None:
        raise HTTPException(
            status_code=404,
            detail="绑定的凭据不存在",
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
    # 真实内容识别
    # -------------------------

    try:
        result = (
            detect_sensitive_columns_with_content(
                db=db,

                source_id=source.id,

                host=source.host,

                port=source.port,

                database_name=
                    source.database_name,

                username=username,

                password=password,

                sample_limit=
                    sample_limit,
            )
        )

    except pymysql.MySQLError as exc:

        db.rollback()

        write_audit(
            db=db,
            request=request,
            user=user,
            action="CONTENT_DETECT",
            resource=
                "sensitive:content_detect",
            result="FAILED",
            policy_id=
                decision.policy_id,
            object_count=0,
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "敏感字段内容识别失败："
                f"{exc}"
            ),
        ) from exc

    finally:
        if "password" in locals():
            del password

    # -------------------------
    # 审计
    # -------------------------

    write_audit(
        db=db,
        request=request,
        user=user,
        action="CONTENT_DETECT",
        resource="sensitive:content_detect",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=result[
            "total_columns"
        ],
    )

    return success(
        request,
        {
            "source_id":
                source.id,

            "source_code":
                source.source_code,

            "database_name":
                source.database_name,

            **result,
        },
        message="敏感字段内容融合识别完成",
    )


@router.get("")
def get_sensitive_fields(
    request: Request,
    source_id: int | None = None,
    is_sensitive: bool | None = None,
    review_status: str | None = None,
    sensitivity_level: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    查询敏感字段画像列表。
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="sensitive:list",
        action="LIST_SENSITIVE",
    )

    results = list_sensitive_field_profiles(
        db=db,
        source_id=source_id,
        is_sensitive=is_sensitive,
        review_status=review_status,
        sensitivity_level=sensitivity_level,
    )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="LIST_SENSITIVE",
        resource="sensitive:list",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=len(results),
    )

    return success(
        request,
        {
            "total": len(results),
            "items": results,
        },
        message="敏感字段列表获取成功",
    )


@router.patch("/{profile_id}/review")
def review_sensitive_field_profile(
    profile_id: int,
    payload: SensitiveFieldReviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    人工复核敏感字段。

    confirmed：
        确认识别结果

    rejected：
        驳回自动识别结果
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="sensitive:review",
        action="REVIEW_SENSITIVE",
    )

    profile = review_sensitive_field(
        db=db,
        profile_id=profile_id,
        review_status=payload.review_status,
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="敏感字段画像不存在",
        )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="REVIEW_SENSITIVE",
        resource="sensitive:review",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        {
            "profile_id":
                profile.id,

            "column_asset_id":
                profile.column_asset_id,

            "is_sensitive":
                profile.is_sensitive,

            "sensitive_type":
                profile.sensitive_type,

            "sensitive_label":
                profile.sensitive_label,

            "sensitivity_level":
                profile.sensitivity_level,

            "review_status":
                profile.review_status,
        },
        message="敏感字段复核完成",
    )