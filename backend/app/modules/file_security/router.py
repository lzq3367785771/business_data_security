from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)

from fastapi.responses import Response

from sqlalchemy.orm import Session

from app.core.authorization import (
    require_policy,
)

from app.core.dependencies import (
    get_current_user,
)

from app.db.models import User
from app.db.session import get_db

from app.modules.audit.service import (
    write_audit,
)

from app.modules.file_security.service import (
    MAX_FILE_SIZE,
    build_secure_file,
    calculate_sha256,
    normalize_filename,
    restore_secure_file,
)


router = APIRouter(
    prefix="/api/v1/file-security",
    tags=["File Security"],
)


@router.post("/encrypt")
async def encrypt_file(
    request: Request,

    file: UploadFile = File(...),

    db: Session = Depends(
        get_db
    ),

    user: User = Depends(
        get_current_user
    ),
):

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="file_security:encrypt",
        action="FILE_ENCRYPT",
    )


    filename = normalize_filename(
        file.filename
        or "uploaded_file"
    )


    data = await file.read()


    if not data:
        raise HTTPException(
            status_code=400,
            detail="上传文件不能为空",
        )


    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="文件大小超过 10 MB 限制",
        )


    try:

        encrypted = build_secure_file(
            filename=filename,
            content_type=(
                file.content_type
                or "application/octet-stream"
            ),
            data=data,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


    sha256 = calculate_sha256(
        data
    )


    write_audit(
        db=db,
        request=request,
        user=user,
        action="FILE_ENCRYPT",
        resource="file_security:encrypt",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
        details={
            "filename":
                filename,

            "original_size":
                len(data),

            "encrypted_size":
                len(encrypted),

            "sha256":
                sha256,

            "content_type":
                file.content_type,
        },
    )


    output_filename = (
        f"{filename}.bdsec"
    )


    encoded_filename = quote(
        output_filename
    )


    return Response(
        content=encrypted,
        media_type=(
            "application/octet-stream"
        ),
        headers={
            "Content-Disposition":
                (
                    "attachment; "
                    f"filename*=UTF-8''"
                    f"{encoded_filename}"
                ),

            "X-Original-SHA256":
                sha256,
        },
    )


@router.post("/decrypt")
async def decrypt_file(
    request: Request,

    file: UploadFile = File(...),

    db: Session = Depends(
        get_db
    ),

    user: User = Depends(
        get_current_user
    ),
):

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="file_security:decrypt",
        action="FILE_DECRYPT",
    )


    encrypted_data = await file.read()


    if not encrypted_data:
        raise HTTPException(
            status_code=400,
            detail="加密文件不能为空",
        )


    try:

        restored = restore_secure_file(
            encrypted_data
        )

    except ValueError as exc:

        write_audit(
            db=db,
            request=request,
            user=user,
            action="FILE_DECRYPT",
            resource="file_security:decrypt",
            result="DENY",
            policy_id=decision.policy_id,
            object_count=0,
            details={
                "uploaded_filename":
                    file.filename,

                "reason":
                    str(exc),
            },
        )


        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


    write_audit(
        db=db,
        request=request,
        user=user,
        action="FILE_DECRYPT",
        resource="file_security:decrypt",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
        details={
            "filename":
                restored["filename"],

            "size":
                restored["size"],

            "sha256":
                restored["sha256"],

            "content_type":
                restored["content_type"],
        },
    )


    encoded_filename = quote(
        restored["filename"]
    )


    return Response(
        content=restored["data"],
        media_type=(
            restored["content_type"]
            or "application/octet-stream"
        ),
        headers={
            "Content-Disposition":
                (
                    "attachment; "
                    f"filename*=UTF-8''"
                    f"{encoded_filename}"
                ),

            "X-File-SHA256":
                restored["sha256"],
        },
    )