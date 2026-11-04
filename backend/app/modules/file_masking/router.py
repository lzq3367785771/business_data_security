
import json

from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)

from fastapi.responses import Response

from pydantic import ValidationError

from sqlalchemy.orm import Session

from app.core.authorization import require_policy
from app.core.dependencies import get_current_user
from app.core.responses import success

from app.db.models import User
from app.db.session import get_db

from app.modules.audit.service import write_audit

from app.modules.file_masking.schemas import MaskRequest

from app.modules.file_masking.service import (
    MAX_FILE_SIZE,
    FileMaskingValidationError,
    preview_file,
    mask_file as build_masked_file,
)


router = APIRouter(
    prefix="/api/v1/file-masking",
    tags=["File Masking"],
)


@router.post("/preview")
async def preview_file_masking(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="file_masking:preview",
        action="FILE_MASK_PREVIEW",
    )

    filename = file.filename or ""

    data = await file.read(MAX_FILE_SIZE + 1)

    try:
        result = preview_file(
            filename=filename,
            content=data,
        )

    except FileMaskingValidationError as exc:

        write_audit(
            db=db,
            request=request,
            user=user,
            action="FILE_MASK_PREVIEW",
            resource="file_masking:preview",
            result="DENY",
            policy_id=decision.policy_id,
            object_count=0,
            details={
                "filename": filename[:255],
                "uploaded_size": len(data),
                "reason": str(exc),
            },
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()

    write_audit(
        db=db,
        request=request,
        user=user,
        action="FILE_MASK_PREVIEW",
        resource="file_masking:preview",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
        details={
            "filename": result["filename"],
            "file_type": result["file_type"],
            "size_bytes": result["size_bytes"],
            "sheet_count": len(result["sheets"]),
            "sensitive_column_count": (
                result["total_sensitive_columns"]
            ),
        },
    )

    return success(
        request,
        result,
        message="文件敏感字段识别完成",
    )


@router.post("/mask")
async def mask_file_download(
    request: Request,
    file: UploadFile = File(...),
    selections: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    根据用户确认的敏感字段执行脱敏，
    返回脱敏后的文件副本。
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="file_masking:mask",
        action="FILE_MASK_EXECUTE",
    )

    filename = file.filename or ""

    data = await file.read(MAX_FILE_SIZE + 1)

    try:
        try:
            parsed = json.loads(selections)

            mask_request = MaskRequest(
                selections=parsed
            )

        except (
            json.JSONDecodeError,
            ValidationError,
            TypeError,
        ) as exc:

            raise FileMaskingValidationError(
                "脱敏字段选择格式无效，请提交合法 JSON 数组"
            ) from exc

        normalized_selections = [
            (
                item.model_dump()
                if hasattr(item, "model_dump")
                else item.dict()
            )
            for item in mask_request.selections
        ]

        result = build_masked_file(
            filename=filename,
            content=data,
            selections=normalized_selections,
        )

    except FileMaskingValidationError as exc:

        write_audit(
            db=db,
            request=request,
            user=user,
            action="FILE_MASK_EXECUTE",
            resource="file_masking:mask",
            result="DENY",
            policy_id=decision.policy_id,
            object_count=0,
            details={
                "filename": filename[:255],
                "uploaded_size": len(data),
                "reason": str(exc),
            },
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()

    write_audit(
        db=db,
        request=request,
        user=user,
        action="FILE_MASK_EXECUTE",
        resource="file_masking:mask",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=result["processed_cells"],
        details={
            "original_filename": filename[:255],
            "output_filename": result["filename"],
            "file_type": result["file_type"],
            "original_size": result["original_size"],
            "output_size": result["output_size"],
            "processed_cells": result["processed_cells"],
            "selections": result["selections"],
        },
    )

    encoded_filename = quote(
        result["filename"],
        safe="",
    )

    return Response(
        content=result["content"],
        media_type=result["media_type"],
        headers={
            "Content-Disposition": (
                "attachment; filename*=UTF-8''"
                f"{encoded_filename}"
            ),
            "X-Masked-Cell-Count": str(
                result["processed_cells"]
            ),
        },
    )
