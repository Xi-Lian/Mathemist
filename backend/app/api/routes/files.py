"""
本地资源文件访问路由。
"""

import mimetypes
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.config_manager import config_manager

router = APIRouter()


def _safe_roots() -> list[Path]:
    learning_root = Path(config_manager.get_learning_resource_path()).resolve()
    export_root = Path(config_manager.get_export_path()).resolve()
    return [learning_root, export_root]


def _resolve_relative_file(path_value: str) -> Path:
    decoded = unquote((path_value or "").strip())
    if not decoded:
        raise HTTPException(status_code=400, detail="缺少 path 参数")

    raw_path = Path(decoded)
    roots = _safe_roots()

    if raw_path.is_absolute():
        candidate = raw_path.resolve()
        for root in roots:
            try:
                candidate.relative_to(root)
                return candidate
            except ValueError:
                continue
        raise HTTPException(status_code=403, detail="不允许访问该路径")

    for root in roots:
        candidate = (root / raw_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if candidate.exists():
            return candidate

    raise HTTPException(status_code=404, detail="文件不存在")


@router.get("/open")
async def open_local_file(path: str = Query(..., description="相对于 learning_resource 的文件路径")):
    target = _resolve_relative_file(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="目标不是文件")

    media_type, _ = mimetypes.guess_type(str(target))
    return FileResponse(
        path=target,
        media_type=media_type or "application/octet-stream",
        filename=target.name,
    )
