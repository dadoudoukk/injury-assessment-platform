from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, make_response, require_permission, require_user
from api.helpers import appraisal_agency_row
from models import AppraisalAgency, CaseRecord
from schemas.business import AppraisalAgencyAudit, AppraisalAgencyCreate, AppraisalAgencyUpdate

router = APIRouter(prefix="/biz/agency", tags=["业务-鉴定机构管理"])

VALID_AGENCY_STATUS = (0, 1, 2, 3)
AUDIT_TARGET_STATUS = (1, 3)


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


@router.get("")
async def agency_list(
    pageNum: int = Query(1, ge=1, description="当前页码"),
    pageSize: int = Query(10, ge=1, le=200, description="每页条数"),
    agencyName: Optional[str] = Query(None, description="机构名称模糊搜索"),
    contactPerson: Optional[str] = Query(None, description="联系人模糊搜索"),
    status: Optional[int] = Query(None, description="状态：0待审核 1正常 2已停用 3审核驳回"),
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

    stmt = select(AppraisalAgency).where(AppraisalAgency.is_delete == 0)
    stmt = _apply_agency_list_filters(
        stmt,
        agency_name=agencyName,
        contact_person=contactPerson,
        status=status,
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

    now = datetime.utcnow()
    db.add(
        AppraisalAgency(
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
    )
    await db.commit()
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

    if row.status != 0:
        return make_response(500, data={}, msg="仅待审核状态的机构可进行审核")

    if body.status == 1:
        row.status = 1
        row.audit_remark = None
        msg = "审核通过"
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

    row.updated_at = datetime.utcnow()
    await db.commit()
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
