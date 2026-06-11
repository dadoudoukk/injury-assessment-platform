import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Header, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from api.deps import make_response, require_user
from core.file_validate import validate_video_upload
from core.paths import UPLOAD_DIR

router = APIRouter(prefix="/file", tags=["文件上传"])


@router.post("/upload")
@router.post("/upload/img")
async def file_upload(
    request: Request,
    file: UploadFile = File(...),
    category: Optional[str] = Query(None, description="上传类别：video 时强制视频 Magic Bytes 校验"),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    orig = (file.filename or "file").strip()
    suffix = Path(orig).suffix
    if suffix:
        suffix = suffix.lower()
    else:
        suffix = ""
    new_name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / new_name
    try:
        def _save_upload() -> None:
            with dest.open("wb") as out:
                shutil.copyfileobj(file.file, out)

        await run_in_threadpool(_save_upload)
    finally:
        await file.close()

    file_size = dest.stat().st_size
    if (category or "").strip().lower() == "video":
        err = validate_video_upload(dest, file_size)
        if err:
            dest.unlink(missing_ok=True)
            return make_response(500, data={}, msg=err)

    base = str(request.base_url).rstrip("/")
    file_url = f"{base}/uploads/{new_name}"
    return make_response(200, data={"fileUrl": file_url}, msg="上传成功")


@router.post("/upload/video")
async def video_upload(
    request: Request,
    file: UploadFile = File(...),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    """鉴定视频专用上传入口，强制 Magic Bytes 校验。"""
    return await file_upload(
        request=request,
        file=file,
        category="video",
        x_access_token=x_access_token,
    )
