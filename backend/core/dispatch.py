"""案件自动派单：合作范围、区域开放配置与机构办公地址匹配。"""

from __future__ import annotations

from typing import Iterable, List, Optional, Set

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.region import city_equivalent_values, normalize_region
from models import AppraisalAgency, BizAgencyServiceScope, BizRegionConfig


def region_scope_matches(
    scope_province: str,
    scope_city: str,
    scope_district: str,
    case_province: str,
    case_city: str,
    case_district: str,
) -> bool:
    """判断机构合作范围是否覆盖案件报案地区。"""
    cp, cc, cd = normalize_region(case_province, case_city, case_district)
    sp, sc, sd = normalize_region(scope_province, scope_city or "", scope_district or "")
    if sp != cp:
        return False
    if not sc:
        return True
    case_variants = set(city_equivalent_values(cp, cc))
    scope_variants = set(city_equivalent_values(sp, sc))
    if not case_variants.intersection(scope_variants):
        return False
    if not sd:
        return True
    return sd == cd


async def is_case_region_enabled(db: AsyncSession, province: str, city: str, district: str) -> bool:
    """区域配置表为空时默认全部开放；非空时须存在 enabled=1 的匹配规则。"""
    total = int((await db.scalar(select(func.count()).select_from(BizRegionConfig))) or 0)
    if total == 0:
        return True

    cp, cc, cd = normalize_region(province, city, district)
    rows = list((await db.scalars(select(BizRegionConfig).where(BizRegionConfig.enabled == 1))).all())
    for row in rows:
        if region_scope_matches(row.province, row.city, row.district, cp, cc, cd):
            return True
    return False


async def _active_agency_ids_with_scopes(db: AsyncSession) -> Set[int]:
    stmt = select(BizAgencyServiceScope.agency_id).distinct()
    return {int(x) for x in (await db.scalars(stmt)).all()}


async def _pick_scoped_agency(
    db: AsyncSession,
    province: str,
    city: str,
    district: str,
    excluded: Set[int],
    *,
    district_level: bool,
) -> Optional[int]:
    scopes = list((await db.scalars(select(BizAgencyServiceScope))).all())
    if not scopes:
        return None

    candidate_ids: List[int] = []
    for scope in scopes:
        if excluded and int(scope.agency_id) in excluded:
            continue
        if district_level and scope.district:
            if not region_scope_matches(scope.province, scope.city, scope.district, province, city, district):
                continue
        elif not district_level:
            if scope.district:
                if not region_scope_matches(scope.province, scope.city, "", province, city, district):
                    continue
            elif not region_scope_matches(scope.province, scope.city, scope.district, province, city, district):
                continue
        else:
            continue
        candidate_ids.append(int(scope.agency_id))

    if not candidate_ids:
        return None

    stmt = (
        select(AppraisalAgency.id)
        .where(
            AppraisalAgency.id.in_(candidate_ids),
            AppraisalAgency.status == 1,
            AppraisalAgency.is_delete == 0,
        )
        .order_by(AppraisalAgency.id.asc())
        .limit(1)
    )
    return (await db.scalars(stmt)).first()


async def _pick_office_location_agency(
    db: AsyncSession,
    province: str,
    city: str,
    district: str,
    excluded: Set[int],
    *,
    district_level: bool,
    agencies_with_scope: Set[int],
) -> Optional[int]:
    city_variants = city_equivalent_values(province, city)
    stmt = select(AppraisalAgency.id).where(
        AppraisalAgency.province == province,
        AppraisalAgency.city.in_(city_variants),
        AppraisalAgency.status == 1,
        AppraisalAgency.is_delete == 0,
    )
    if agencies_with_scope:
        stmt = stmt.where(AppraisalAgency.id.notin_(agencies_with_scope))
    if district_level:
        stmt = stmt.where(AppraisalAgency.district == district)
    if excluded:
        stmt = stmt.where(AppraisalAgency.id.notin_(excluded))
    return (await db.scalars(stmt.limit(1))).first()


async def auto_dispatch_agency(
    db: AsyncSession,
    province: str,
    city: str,
    district: str,
    exclude_agency_ids: Optional[Iterable[int]] = None,
) -> Optional[int]:
    """自动派单：先同区县再同市；优先合作范围，无范围时回退机构办公地址。"""
    if not await is_case_region_enabled(db, province, city, district):
        return None

    province, city, district = normalize_region(province, city, district)
    excluded = {int(x) for x in (exclude_agency_ids or []) if x is not None}
    agencies_with_scope = await _active_agency_ids_with_scopes(db)

    for district_level in (True, False):
        agency_id = await _pick_scoped_agency(
            db, province, city, district, excluded, district_level=district_level
        )
        if agency_id is not None:
            return agency_id
        agency_id = await _pick_office_location_agency(
            db,
            province,
            city,
            district,
            excluded,
            district_level=district_level,
            agencies_with_scope=agencies_with_scope,
        )
        if agency_id is not None:
            return agency_id
    return None
