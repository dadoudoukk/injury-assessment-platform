from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, make_response, require_permission, require_user
from api.agency_user import bind_agency_admin_user
from api.helpers import appraisal_agency_row
from core.config import is_audit_first_agency_onboard
from core.context import ctx_user_id
from core.region import normalize_region
from models import AppraisalAgency, BizAgencyRejectLog, BizAgencyServiceScope, CaseRecord
from schemas.business import (
    AgencyServiceScopeCreate,
    AppraisalAgencyAudit,
    AppraisalAgencyCreate,
    AppraisalAgencyUpdate,
)
from services.audit_service import (
    BIZ_TYPE_AGENCY_ONBOARD,
    approve_audit,
    build_agency_onboard_payload,
    create_audit_record,
    get_pending_audit,
    has_any_audit_record,
    reject_audit,
)

router = APIRouter(prefix="/biz/agency", tags=["业务-鉴定机构管理"])

VALID_AGENCY_STATUS = (0, 1, 2, 3)
AUDIT_TARGET_STATUS = (1, 3)

_CASE_STATUS_LABELS = {
    1: "待确认",
    2: "已受理",
    3: "鉴定中",
    4: "已完成",
    5: "已打回",
    6: "报告待平台审核",
}


def _reject_log_row(
    log: BizAgencyRejectLog,
    *,
    agency_name_map: Dict[int, str],
    case: Optional[CaseRecord],
) -> Dict[str, Any]:
    current_agency_id = case.agency_id if case else log.new_agency_id
    current_name = None
    if current_agency_id is not None:
        current_name = agency_name_map.get(int(current_agency_id))
    case_status = int(case.status) if case else 0
    return {
        "id": str(log.id),
        "caseId": str(log.case_id),
        "reportNumber": log.report_number,
        "victimName": log.victim_name,
        "rejectedAgencyId": int(log.agency_id),
        "rejectedAgencyName": agency_name_map.get(int(log.agency_id), "未知机构"),
        "currentAgencyId": current_agency_id,
        "currentAgencyName": current_name,
        "caseStatus": case_status,
        "caseStatusLabel": _CASE_STATUS_LABELS.get(case_status, "未知"),
        "recordTime": log.rejected_at.strftime("%Y-%m-%d %H:%M:%S") if log.rejected_at else "",
    }


def _parse_agency_id(agency_id: Union[str, int]) -> Optional[int]:
    try:
        return int(agency_id)
    except (TypeError, ValueError):
        return None


def _apply_agency_list_filters(
    stmt,
    *,
    agency_name: Optional[str],
    contact_person: Optional[str],
    status: Optional[int],
    exclude_status: Optional[int],
    province: Optional[str],
    city: Optional[str],
    district: Optional[str],
):
    if agency_name and agency_name.strip():
        stmt = stmt.where(AppraisalAgency.agency_name.like(f"%{agency_name.strip()}%"))
    if contact_person and contact_person.strip():
        stmt = stmt.where(AppraisalAgency.contact_person.like(f"%{contact_person.strip()}%"))
    if status is not None:
        stmt = stmt.where(AppraisalAgency.status == status)
    if exclude_status is not None:
        stmt = stmt.where(AppraisalAgency.status != exclude_status)
    if province and province.strip():
        stmt = stmt.where(AppraisalAgency.province == province.strip())
    if city and city.strip():
        stmt = stmt.where(AppraisalAgency.city == city.strip())
    if district and district.strip():
        stmt = stmt.where(AppraisalAgency.district == district.strip())
    return stmt


async def _agency_name_exists(
    db: AsyncSession,
    agency_name: str,
    exclude_id: Optional[int] = None,
) -> bool:
    stmt = select(AppraisalAgency.id).where(
        AppraisalAgency.agency_name == agency_name,
        AppraisalAgency.is_delete == 0,
    )
    if exclude_id is not None:
        stmt = stmt.where(AppraisalAgency.id != exclude_id)
    stmt = stmt.limit(1)
    return (await db.scalars(stmt)).first() is not None


def _update_payload_has_changes(row: AppraisalAgency, body: AppraisalAgencyUpdate) -> bool:
    """判断普通编辑是否携带了业务字段变更（用于驳回后重新提交审核）。"""
    if body.agencyName is not None and body.agencyName.strip() != row.agency_name:
        return True
    if body.contactPerson is not None and body.contactPerson.strip() != row.contact_person:
        return True
    if body.contactPhone is not None and body.contactPhone.strip() != row.contact_phone:
        return True
    if body.province is not None and body.province.strip() != row.province:
        return True
    if body.city is not None and body.city.strip() != row.city:
        return True
    if body.district is not None and body.district.strip() != row.district:
        return True
    if body.address is not None and body.address.strip() != row.address:
        return True
    return False


async def _create_agency_with_optional_audit(
    db: AsyncSession,
    *,
    agency_name: str,
    contact_person: str,
    contact_phone: str,
    province: str,
    city: str,
    district: str,
    address: str,
    created_by: Optional[int] = None,
) -> AppraisalAgency:
    now = datetime.utcnow()
    agency = AppraisalAgency(
        agency_name=agency_name,
        contact_person=contact_person,
        contact_phone=contact_phone,
        province=province,
        city=city,
        district=district,
        address=address,
        status=0,
        audit_remark=None,
        created_at=now,
        updated_at=now,
    )
    db.add(agency)
    await db.flush()

    if is_audit_first_agency_onboard():
        await create_audit_record(
            db,
            biz_type=BIZ_TYPE_AGENCY_ONBOARD,
            biz_id=agency.id,
            submit_payload=build_agency_onboard_payload(agency),
            created_by=created_by,
        )
    return agency


@router.get("")
async def agency_list(
    pageNum: int = Query(1, ge=1, description="当前页码"),
    pageSize: int = Query(10, ge=1, le=200, description="每页条数"),
    agencyName: Optional[str] = Query(None, description="机构名称模糊搜索"),
    contactPerson: Optional[str] = Query(None, description="联系人模糊搜索"),
    status: Optional[int] = Query(None, description="状态：0待审核 1正常 2已停用 3审核驳回"),
    excludeStatus: Optional[int] = Query(None, description="排除的状态值（如档案页排除 0 待审核）"),
    province: Optional[str] = Query(None, description="省（精确匹配）"),
    city: Optional[str] = Query(None, description="市（精确匹配）"),
    district: Optional[str] = Query(None, description="区县（精确匹配）"),
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    if status is not None and status not in VALID_AGENCY_STATUS:
        return make_response(500, data={}, msg="机构状态参数无效")
    if excludeStatus is not None and excludeStatus not in VALID_AGENCY_STATUS:
        return make_response(500, data={}, msg="排除状态参数无效")

    stmt = select(AppraisalAgency).where(AppraisalAgency.is_delete == 0)
    stmt = _apply_agency_list_filters(
        stmt,
        agency_name=agencyName,
        contact_person=contactPerson,
        status=status,
        exclude_status=excludeStatus,
        province=province,
        city=city,
        district=district,
    )

    count_stmt = select(func.count()).select_from(AppraisalAgency).where(*stmt._where_criteria)
    total = int((await db.scalar(count_stmt)) or 0)

    stmt = stmt.order_by(AppraisalAgency.id.desc())
    stmt = stmt.offset((pageNum - 1) * pageSize).limit(pageSize)
    rows = list((await db.scalars(stmt)).all())
    return make_response(
        200,
        data={
            "list": [appraisal_agency_row(r) for r in rows],
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
        },
        msg="success",
    )


@router.get("/options")
async def agency_options(
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    stmt = (
        select(AppraisalAgency.id, AppraisalAgency.agency_name)
        .where(
            AppraisalAgency.is_delete == 0,
            AppraisalAgency.status == 1,
        )
        .order_by(AppraisalAgency.agency_name.asc(), AppraisalAgency.id.asc())
    )
    rows = (await db.execute(stmt)).all()
    options = [{"id": str(r.id), "agencyName": r.agency_name} for r in rows]
    return make_response(200, data={"list": options}, msg="success")


def _format_region_text(province: str, city: str, district: str) -> str:
    p, c, d = normalize_region(province, city or "", district or "")
    parts = [p]
    if c:
        parts.append(c)
    if d:
        parts.append(d)
    return " / ".join(parts)


def _scope_row(scope: BizAgencyServiceScope, agency_name: str) -> Dict[str, Any]:
    return {
        "id": str(scope.id),
        "agencyId": int(scope.agency_id),
        "agencyName": agency_name,
        "province": scope.province,
        "city": scope.city or "",
        "district": scope.district or "",
        "regionText": _format_region_text(scope.province, scope.city, scope.district),
        "createdAt": scope.created_at.strftime("%Y-%m-%d %H:%M:%S") if scope.created_at else "",
    }


@router.get("/scope", dependencies=[Depends(require_permission("agency:scope:query"))])
async def agency_service_scope_list(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200),
    agencyId: Optional[int] = Query(None, description="机构 ID"),
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    filters = []
    if agencyId is not None:
        filters.append(BizAgencyServiceScope.agency_id == agencyId)

    total = int(
        (await db.scalar(select(func.count()).select_from(BizAgencyServiceScope).where(*filters))) or 0
    )
    scopes = list(
        (
            await db.scalars(
                select(BizAgencyServiceScope)
                .where(*filters)
                .order_by(BizAgencyServiceScope.agency_id.asc(), BizAgencyServiceScope.id.asc())
                .offset((pageNum - 1) * pageSize)
                .limit(pageSize)
            )
        ).all()
    )

    agency_ids = {int(s.agency_id) for s in scopes}
    agency_name_map: Dict[int, str] = {}
    if agency_ids:
        agencies = (
            await db.scalars(
                select(AppraisalAgency).where(
                    AppraisalAgency.id.in_(agency_ids),
                    AppraisalAgency.is_delete == 0,
                )
            )
        ).all()
        agency_name_map = {int(a.id): a.agency_name for a in agencies}

    return make_response(
        200,
        data={
            "list": [_scope_row(s, agency_name_map.get(int(s.agency_id), "未知机构")) for s in scopes],
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
        },
        msg="success",
    )


@router.post("/scope", dependencies=[Depends(require_permission("agency:scope:edit"))])
async def agency_service_scope_create(
    body: AgencyServiceScopeCreate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    agency = (
        await db.scalars(
            select(AppraisalAgency).where(
                AppraisalAgency.id == body.agencyId,
                AppraisalAgency.is_delete == 0,
            )
        )
    ).first()
    if agency is None:
        return make_response(500, data={}, msg="鉴定机构不存在")

    province, city, district = normalize_region(body.province, body.city or "", body.district or "")
    if not province:
        return make_response(500, data={}, msg="省不能为空")

    exists = (
        await db.scalars(
            select(BizAgencyServiceScope.id).where(
                BizAgencyServiceScope.agency_id == body.agencyId,
                BizAgencyServiceScope.province == province,
                BizAgencyServiceScope.city == city,
                BizAgencyServiceScope.district == district,
            ).limit(1)
        )
    ).first()
    if exists is not None:
        return make_response(500, data={}, msg="该合作范围已存在")

    db.add(
        BizAgencyServiceScope(
            agency_id=body.agencyId,
            province=province,
            city=city,
            district=district,
            created_at=datetime.utcnow(),
        )
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return make_response(500, data={}, msg="新增失败：合作范围重复")
    return make_response(200, data={}, msg="新增成功")


@router.delete("/scope/{scope_id}", dependencies=[Depends(require_permission("agency:scope:edit"))])
async def agency_service_scope_delete(
    scope_id: Union[str, int],
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_agency_id(scope_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="合作范围 ID 无效")

    row = await db.get(BizAgencyServiceScope, parsed_id)
    if row is None:
        return make_response(500, data={}, msg="合作范围不存在")

    await db.delete(row)
    await db.commit()
    return make_response(200, data={}, msg="删除成功")


@router.get("/onboard-legacy-pending", dependencies=[Depends(require_permission("agency:query"))])
async def agency_onboard_legacy_pending(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    """无 biz_audit_record 的 status=0 机构（阶段二双读回退）。"""
    from models import BizAuditRecord

    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    audited_ids_stmt = select(BizAuditRecord.biz_id).where(
        BizAuditRecord.biz_type == BIZ_TYPE_AGENCY_ONBOARD,
    )
    filters = [
        AppraisalAgency.is_delete == 0,
        AppraisalAgency.status == 0,
        AppraisalAgency.id.notin_(audited_ids_stmt),
    ]
    total = int((await db.scalar(select(func.count()).select_from(AppraisalAgency).where(*filters))) or 0)
    rows = list(
        (
            await db.scalars(
                select(AppraisalAgency)
                .where(*filters)
                .order_by(AppraisalAgency.created_at.desc(), AppraisalAgency.id.desc())
                .offset((pageNum - 1) * pageSize)
                .limit(pageSize)
            )
        ).all()
    )
    return make_response(
        200,
        data={
            "list": [appraisal_agency_row(row) for row in rows],
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
        },
        msg="success",
    )


@router.get("/reject-log", dependencies=[Depends(require_permission("agency:query"))])
async def agency_reject_log(
    pageNum: int = Query(1, ge=1, description="当前页码"),
    pageSize: int = Query(10, ge=1, le=200, description="每页条数"),
    agencyId: Optional[int] = Query(None, description="拒单机构 ID"),
    reportNumber: Optional[str] = Query(None, description="出险报案号模糊搜索"),
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    filters = []
    if agencyId is not None:
        filters.append(BizAgencyRejectLog.agency_id == agencyId)
    if reportNumber and reportNumber.strip():
        filters.append(BizAgencyRejectLog.report_number.like(f"%{reportNumber.strip()}%"))

    total = int(
        (await db.scalar(select(func.count()).select_from(BizAgencyRejectLog).where(*filters))) or 0
    )
    logs = list(
        (
            await db.scalars(
                select(BizAgencyRejectLog)
                .where(*filters)
                .order_by(BizAgencyRejectLog.rejected_at.desc(), BizAgencyRejectLog.id.desc())
                .offset((pageNum - 1) * pageSize)
                .limit(pageSize)
            )
        ).all()
    )

    case_ids = {int(log.case_id) for log in logs}
    cases_by_id: Dict[int, CaseRecord] = {}
    if case_ids:
        case_rows = (
            await db.scalars(
                select(CaseRecord).where(CaseRecord.id.in_(case_ids), CaseRecord.is_delete == 0)
            )
        ).all()
        cases_by_id = {int(c.id): c for c in case_rows}

    agency_ids: set[int] = set()
    for log in logs:
        agency_ids.add(int(log.agency_id))
        if log.new_agency_id is not None:
            agency_ids.add(int(log.new_agency_id))
        case = cases_by_id.get(int(log.case_id))
        if case and case.agency_id is not None:
            agency_ids.add(int(case.agency_id))

    agency_name_map: Dict[int, str] = {}
    if agency_ids:
        agency_rows = (
            await db.scalars(select(AppraisalAgency).where(AppraisalAgency.id.in_(agency_ids)))
        ).all()
        agency_name_map = {int(row.id): row.agency_name for row in agency_rows}

    page_rows = [
        _reject_log_row(log, agency_name_map=agency_name_map, case=cases_by_id.get(int(log.case_id)))
        for log in logs
    ]
    return make_response(
        200,
        data={"list": page_rows, "pageNum": pageNum, "pageSize": pageSize, "total": total},
        msg="success",
    )


@router.get("/{agency_id}")
async def agency_detail(
    agency_id: Union[str, int],
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_agency_id(agency_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="鉴定机构 ID 无效")

    stmt = select(AppraisalAgency).where(
        AppraisalAgency.id == parsed_id,
        AppraisalAgency.is_delete == 0,
    )
    row = (await db.scalars(stmt)).first()
    if row is None:
        return make_response(500, data={}, msg="鉴定机构不存在")

    return make_response(200, data=appraisal_agency_row(row), msg="success")


@router.post("/register")
async def agency_register(
    body: AppraisalAgencyCreate,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    agency_name = body.agencyName.strip()
    contact_person = body.contactPerson.strip()
    contact_phone = body.contactPhone.strip()
    province = body.province.strip()
    city = body.city.strip()
    district = body.district.strip()
    address = body.address.strip()

    if not agency_name:
        return make_response(500, data={}, msg="机构名称不能为空")
    if await _agency_name_exists(db, agency_name):
        return make_response(500, data={}, msg="机构名称已存在，请确认是否已被注册")

    province, city, district = normalize_region(province, city, district)

    try:
        await _create_agency_with_optional_audit(
            db,
            agency_name=agency_name,
            contact_person=contact_person,
            contact_phone=contact_phone,
            province=province,
            city=city,
            district=district,
            address=address,
        )
        await db.commit()
    except (ValueError, IntegrityError) as exc:
        await db.rollback()
        if isinstance(exc, ValueError):
            return make_response(500, data={}, msg=str(exc))
        return make_response(500, data={}, msg="入驻申请提交失败")
    return make_response(200, data={}, msg="入驻申请已提交，请等待审核")

@router.post("", dependencies=[Depends(require_permission("agency:add"))])
async def agency_create(
    body: AppraisalAgencyCreate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    agency_name = body.agencyName.strip()
    contact_person = body.contactPerson.strip()
    contact_phone = body.contactPhone.strip()
    province = body.province.strip()
    city = body.city.strip()
    district = body.district.strip()
    address = body.address.strip()

    if not agency_name:
        return make_response(500, data={}, msg="机构名称不能为空")
    if not contact_person:
        return make_response(500, data={}, msg="联系人不能为空")
    if not contact_phone:
        return make_response(500, data={}, msg="联系电话不能为空")
    if not province:
        return make_response(500, data={}, msg="省不能为空")
    if not city:
        return make_response(500, data={}, msg="市不能为空")
    if not district:
        return make_response(500, data={}, msg="区县不能为空")
    if not address:
        return make_response(500, data={}, msg="详细地址不能为空")

    if await _agency_name_exists(db, agency_name):
        return make_response(500, data={}, msg="机构名称已存在")

    province, city, district = normalize_region(province, city, district)

    now = datetime.utcnow()
    try:
        await _create_agency_with_optional_audit(
            db,
            agency_name=agency_name,
            contact_person=contact_person,
            contact_phone=contact_phone,
            province=province,
            city=city,
            district=district,
            address=address,
            created_by=ctx_user_id.get(),
        )
        await db.commit()
    except (ValueError, IntegrityError) as exc:
        await db.rollback()
        if isinstance(exc, ValueError):
            return make_response(500, data={}, msg=str(exc))
        return make_response(500, data={}, msg="新增失败")
    return make_response(200, data={}, msg="新增成功")


@router.put("/{agency_id}/audit", dependencies=[Depends(require_permission("agency:audit"))])
async def agency_audit(
    agency_id: Union[str, int],
    body: AppraisalAgencyAudit,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_agency_id(agency_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="鉴定机构 ID 无效")

    if body.status not in AUDIT_TARGET_STATUS:
        return make_response(500, data={}, msg="审核结果无效，仅支持通过(1)或驳回(3)")

    audit_remark = (body.auditRemark or "").strip()
    if body.status == 3 and not audit_remark:
        return make_response(500, data={}, msg="驳回时必须填写驳回原因")

    stmt = select(AppraisalAgency).where(
        AppraisalAgency.id == parsed_id,
        AppraisalAgency.is_delete == 0,
    )
    row = (await db.scalars(stmt)).first()
    if row is None:
        return make_response(500, data={}, msg="鉴定机构不存在")

    pending = await get_pending_audit(db, BIZ_TYPE_AGENCY_ONBOARD, parsed_id)
    if pending is not None:
        if body.status == 1:
            err, suffix = await approve_audit(db, pending.id, ctx_user_id.get())
            if err:
                return make_response(500, data={}, msg=err)
            msg = f"审核通过{suffix}" if suffix else "审核通过"
        else:
            err = await reject_audit(db, pending.id, audit_remark, ctx_user_id.get())
            if err:
                return make_response(500, data={}, msg=err)
            msg = "已驳回"
        return make_response(200, data={}, msg=msg)

    if is_audit_first_agency_onboard():
        if row.status == 0 and not await has_any_audit_record(db, BIZ_TYPE_AGENCY_ONBOARD, parsed_id):
            pass
        else:
            return make_response(500, data={}, msg="未找到待审核记录，无法审核")

    if row.status != 0:
        return make_response(500, data={}, msg="仅待审核状态的机构可进行审核")

    if body.status == 1:
        row.status = 1
        row.audit_remark = None
        suffix, _created = await bind_agency_admin_user(db, row)
        msg = f"审核通过，{suffix}"
    else:
        row.status = 3
        row.audit_remark = audit_remark
        msg = "已驳回"

    row.updated_at = datetime.utcnow()
    await db.commit()
    return make_response(200, data={}, msg=msg)


@router.put("/{agency_id}", dependencies=[Depends(require_permission("agency:edit"))])
async def agency_update(
    agency_id: Union[str, int],
    body: AppraisalAgencyUpdate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_agency_id(agency_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="鉴定机构 ID 无效")

    stmt = select(AppraisalAgency).where(
        AppraisalAgency.id == parsed_id,
        AppraisalAgency.is_delete == 0,
    )
    row = (await db.scalars(stmt)).first()
    if row is None:
        return make_response(500, data={}, msg="鉴定机构不存在")

    was_rejected = row.status == 3
    should_resubmit = was_rejected and _update_payload_has_changes(row, body)

    if body.agencyName is not None:
        agency_name = body.agencyName.strip()
        if not agency_name:
            return make_response(500, data={}, msg="机构名称不能为空")
        if await _agency_name_exists(db, agency_name, exclude_id=parsed_id):
            return make_response(500, data={}, msg="机构名称已存在")
        row.agency_name = agency_name

    if body.contactPerson is not None:
        contact_person = body.contactPerson.strip()
        if not contact_person:
            return make_response(500, data={}, msg="联系人不能为空")
        row.contact_person = contact_person

    if body.contactPhone is not None:
        contact_phone = body.contactPhone.strip()
        if not contact_phone:
            return make_response(500, data={}, msg="联系电话不能为空")
        row.contact_phone = contact_phone

    if body.province is not None:
        province = body.province.strip()
        if not province:
            return make_response(500, data={}, msg="省不能为空")
        row.province = province

    if body.city is not None:
        city = body.city.strip()
        if not city:
            return make_response(500, data={}, msg="市不能为空")
        row.city = city

    if body.district is not None:
        district = body.district.strip()
        if not district:
            return make_response(500, data={}, msg="区县不能为空")
        row.district = district

    if body.address is not None:
        address = body.address.strip()
        if not address:
            return make_response(500, data={}, msg="详细地址不能为空")
        row.address = address

    if should_resubmit:
        row.status = 0
        row.audit_remark = None
        if is_audit_first_agency_onboard():
            try:
                await create_audit_record(
                    db,
                    biz_type=BIZ_TYPE_AGENCY_ONBOARD,
                    biz_id=parsed_id,
                    submit_payload=build_agency_onboard_payload(row),
                    created_by=ctx_user_id.get(),
                )
            except ValueError as exc:
                await db.rollback()
                msg = str(exc)
                if "存在待审核记录" in msg:
                    return make_response(500, data={}, msg="已有一条待审核记录，请勿重复提交")
                return make_response(500, data={}, msg=msg)
            except IntegrityError:
                await db.rollback()
                return make_response(500, data={}, msg="重新提交审核失败：存在并发冲突或重复待审记录")

    row.province, row.city, row.district = normalize_region(row.province, row.city, row.district)

    row.updated_at = datetime.utcnow()
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return make_response(500, data={}, msg="修改失败")
    return make_response(200, data={}, msg="修改成功")


@router.delete("/{agency_id}", dependencies=[Depends(require_permission("agency:delete"))])
async def agency_delete(
    agency_id: Union[str, int],
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_agency_id(agency_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="鉴定机构 ID 无效")

    stmt = select(AppraisalAgency).where(
        AppraisalAgency.id == parsed_id,
        AppraisalAgency.is_delete == 0,
    )
    row = (await db.scalars(stmt)).first()
    if row is None:
        return make_response(500, data={}, msg="鉴定机构不存在")

    case_stmt = (
        select(CaseRecord.id)
        .where(CaseRecord.agency_id == parsed_id, CaseRecord.is_delete == 0)
        .limit(1)
    )
    if (await db.scalars(case_stmt)).first() is not None:
        return make_response(500, data={}, msg="该鉴定机构已关联案件，无法删除")

    row.is_delete = 1
    row.delete_time = datetime.utcnow()
    row.updated_at = datetime.utcnow()
    await db.commit()
    return make_response(200, data={}, msg="删除成功")
