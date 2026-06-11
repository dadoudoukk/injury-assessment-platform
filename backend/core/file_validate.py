"""上传文件 Magic Bytes 校验（只信文件头，不信扩展名）。"""

from pathlib import Path
from typing import Optional, Tuple

# 常见视频容器魔数
_VIDEO_CHECKS: Tuple[Tuple[int, bytes, Optional[bytes]], ...] = (
    # MP4 / MOV / M4V：offset 4 起为 ftyp
    (4, b"ftyp", None),
    # WebM / MKV
    (0, b"\x1a\x45\xdf\xa3", None),
    # AVI：RIFF....AVI
    (0, b"RIFF", b"AVI "),
    # MPEG-PS
    (0, b"\x00\x00\x01\xba", None),
    (0, b"\x00\x00\x01\xb3", None),
)

MAX_VIDEO_BYTES = 100 * 1024 * 1024  # 100MB
MAX_VIDEO_COUNT = 9


def read_file_header(path: Path, size: int = 32) -> bytes:
    with path.open("rb") as f:
        return f.read(size)


def is_video_content(header: bytes) -> bool:
    if len(header) < 12:
        return False
    for offset, sig, extra in _VIDEO_CHECKS:
        if len(header) < offset + len(sig):
            continue
        if header[offset : offset + len(sig)] != sig:
            continue
        if extra is not None:
            if len(header) < 8 + len(extra):
                continue
            if header[8 : 8 + len(extra)] != extra:
                continue
        return True
    return False


def validate_video_upload(path: Path, file_size: int) -> Optional[str]:
    """校验视频文件，通过返回 None，否则返回错误文案。"""
    if file_size <= 0:
        return "文件为空"
    if file_size > MAX_VIDEO_BYTES:
        return f"视频大小不能超过 {MAX_VIDEO_BYTES // (1024 * 1024)}MB"
    header = read_file_header(path)
    if not is_video_content(header):
        return "仅支持上传视频文件（MP4/MOV/WebM/AVI 等），检测到非视频格式"
    return None
