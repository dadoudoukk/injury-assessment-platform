from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, make_response, require_permission, require_user
from core.region import normalize_region
from models import BizRegionConfig
from schemas.business import RegionConfigCreate, RegionConfigUpdate

router = APIRouter(prefix="/biz/region", tags=["业务-区域配置"])


def _format_region_text(province: str, city: str, district: str) -> str:
    p, c, d = normalize_region(province, city or "", district or "")
    parts = [p]
    if c:
        parts.append(c)
    if d:
        parts.append(d)
    return " / ".join(parts)


def _region_row(row: BizRegionConfig) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "province": row.province,
        "city": row.city or "",
        "district": row.district or "",
        "regionText": _format_region_text(row.province, row.city, row.district),
        "enabled": int(row.enabled),
        "sort": int(row.sort),
        "remark": row.remark or "",
        "createdAt": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else "",
        "updatedAt": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else "",
    }


def _parse_id(value: Union[str, int]) -> Optional[int]:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else None
    except (TypeError, ValueError):
        return None


@router.get("", dependencies=[Depends(require_permission("region:query"))])
async def region_config_list(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200),
    province: Optional[str] = Query(None, description="省"),
    enabled: Optional[int] = Query(None, description="1启用 0停用"),
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    filters = []
    if province and province.strip():
        filters.append(BizRegionConfig.province.like(f"%{province.strip()}%"))
    if enabled is not None:
        filters.append(BizRegionConfig.enabled == enabled)

    total = int((await db.scalar(select(func.count()).select_from(BizRegionConfig).where(*filters))) or 0)
    rows = list(
        (
            await db.scalars(
                select(BizRegionConfig)
                .where(*filters)
                .order_by(BizRegionConfig.sort.asc(), BizRegionConfig.id.asc())
                .offset((pageNum - 1) * pageSize)
                .limit(pageSize)
            )
        ).all()
    )
    return make_response(
        200,
        data={"list": [_region_row(row) for row in rows], "pageNum": pageNum, "pageSize": pageSize, "total": total},
        msg="success",
    )


@router.post("", dependencies=[Depends(require_permission("region:edit"))])
async def region_config_create(
    body: RegionConfigCreate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    province, city, district = normalize_region(body.province, body.city or "", body.district or "")
    if not province:
        return make_response(500, data={}, msg="省不能为空")
    if body.enabled not in (0, 1):
        return make_response(500, data={}, msg="enabled 参数无效")

    exists = (
        await db.scalars(
            select(BizRegionConfig.id).where(
                BizRegionConfig.province == province,
                BizRegionConfig.city == city,
                BizRegionConfig.district == district,
            ).limit(1)
        )
    ).first()
    if exists is not None:
        return make_response(500, data={}, msg="该区域配置已存在")

    now = datetime.utcnow()
    row = BizRegionConfig(
        province=province,
        city=city,
        district=district,
        enabled=body.enabled,
        sort=body.sort,
        remark=(body.remark or "").strip() or None,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return make_response(500, data={}, msg="新增失败：区域重复")
    return make_response(200, data={}, msg="新增成功")


@router.put("/{config_id}", dependencies=[Depends(require_permission("region:edit"))])
async def region_config_update(
    config_id: Union[str, int],
    body: RegionConfigUpdate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_id(config_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="配置 ID 无效")

    row = await db.get(BizRegionConfig, parsed_id)
    if row is None:
        return make_response(500, data={}, msg="区域配置不存在")

    if body.enabled is not None:
        if body.enabled not in (0, 1):
            return make_response(500, data={}, msg="enabled 参数无效")
        row.enabled = body.enabled
    if body.sort is not None:
        row.sort = body.sort
    if body.remark is not None:
        row.remark = body.remark.strip() or None

    row.updated_at = datetime.utcnow()
    await db.commit()
    return make_response(200, data={}, msg="修改成功")


@router.delete("/{config_id}", dependencies=[Depends(require_permission("region:edit"))])
async def region_config_delete(
    config_id: Union[str, int],
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_id(config_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="配置 ID 无效")

    row = await db.get(BizRegionConfig, parsed_id)
    if row is None:
        return make_response(500, data={}, msg="区域配置不存在")

    await db.delete(row)
    await db.commit()
    return make_response(200, data={}, msg="删除成功")
