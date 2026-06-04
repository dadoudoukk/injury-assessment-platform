from datetime import date, datetime
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, make_response, require_permission, require_user_with_data_perm
from api.helpers import case_record_row
from core.context import ctx_dept_id, ctx_user_id
from core.data_perm import apply_data_scope
from models import CaseRecord
from schemas.business import CaseRecordCreate, CaseRecordUpdate

router = APIRouter(prefix="/biz/case", tags=["业务-案件管理"])

VALID_CASE_STATUS = (1, 2, 3)


def _parse_case_id(case_id: Union[str, int]) -> Optional[int]:
    try:
        return int(case_id)
    except (TypeError, ValueError):
        return None


def _apply_case_list_filters(
    stmt,
    *,
    report_number: Optional[str],
    victim_name: Optional[str],
    status: Optional[int],
    insurance_company: Optional[str],
    report_date_start: Optional[date],
    report_date_end: Optional[date],
):
    if report_number and report_number.strip():
        stmt = stmt.where(CaseRecord.report_number.like(f"%{report_number.strip()}%"))
    if victim_name and victim_name.strip():
        stmt = stmt.where(CaseRecord.victim_name.like(f"%{victim_name.strip()}%"))
    if status is not None:
        stmt = stmt.where(CaseRecord.status == status)
    if insurance_company and insurance_company.strip():
        stmt = stmt.where(CaseRecord.insurance_company == insurance_company.strip())
    if report_date_start is not None:
        stmt = stmt.where(CaseRecord.report_date >= report_date_start)
    if report_date_end is not None:
        stmt = stmt.where(CaseRecord.report_date <= report_date_end)
    return stmt


@router.get("")
async def case_list(
    pageNum: int = Query(1, ge=1, description="当前页码"),
    pageSize: int = Query(10, ge=1, le=200, description="每页条数"),
    reportNumber: Optional[str] = Query(None, description="出险报案号模糊搜索"),
    victimName: Optional[str] = Query(None, description="伤者姓名模糊搜索"),
    status: Optional[int] = Query(None, description="案件状态：1待接单 2鉴定中 3已完成"),
    insuranceCompany: Optional[str] = Query(None, description="所属保险公司（精确匹配）"),
    reportDateStart: Optional[date] = Query(None, description="报案日期起（含）"),
    reportDateEnd: Optional[date] = Query(None, description="报案日期止（含）"),
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    if reportDateStart and reportDateEnd and reportDateStart > reportDateEnd:
        return make_response(500, data={}, msg="报案日期起不能晚于报案日期止")

    stmt = select(CaseRecord).where(CaseRecord.is_delete == 0)
    stmt = _apply_case_list_filters(
        stmt,
        report_number=reportNumber,
        victim_name=victimName,
        status=status,
        insurance_company=insuranceCompany,
        report_date_start=reportDateStart,
        report_date_end=reportDateEnd,
    )
    stmt = apply_data_scope(stmt, CaseRecord)

    count_stmt = select(func.count()).select_from(CaseRecord).where(*stmt._where_criteria)
    total = int((await db.scalar(count_stmt)) or 0)

    stmt = stmt.order_by(CaseRecord.id.desc())
    stmt = stmt.offset((pageNum - 1) * pageSize).limit(pageSize)
    rows = list((await db.scalars(stmt)).all())
    return make_response(
        200,
        data={
            "list": [case_record_row(r) for r in rows],
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
        },
        msg="success",
    )


@router.get("/{case_id}")
async def case_detail(
    case_id: Union[str, int],
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_case_id(case_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="案件 ID 无效")

    stmt = select(CaseRecord).where(CaseRecord.id == parsed_id, CaseRecord.is_delete == 0)
    stmt = apply_data_scope(stmt, CaseRecord)
    row = (await db.scalars(stmt)).first()
    if row is None:
        return make_response(500, data={}, msg="案件不存在或无权访问")

    return make_response(200, data=case_record_row(row), msg="success")


@router.post("", dependencies=[Depends(require_permission("case:add"))])
async def case_create(
    body: CaseRecordCreate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    if body.status not in VALID_CASE_STATUS:
        return make_response(500, data={}, msg="案件状态参数无效")

    report_number = body.reportNumber.strip()
    victim_name = body.victimName.strip()
    victim_phone = body.victimPhone.strip()
    province = body.province.strip()
    city = body.city.strip()
    district = body.district.strip()
    accident_type = body.accidentType.strip()
    injury_type = body.injuryType.strip()
    insurance_company = body.insuranceCompany.strip()
    if not report_number:
        return make_response(500, data={}, msg="出险报案号不能为空")
    if not victim_name:
        return make_response(500, data={}, msg="伤者姓名不能为空")
    if not victim_phone:
        return make_response(500, data={}, msg="联系电话不能为空")
    if not province:
        return make_response(500, data={}, msg="报案省份不能为空")
    if not city:
        return make_response(500, data={}, msg="报案城市不能为空")
    if not district:
        return make_response(500, data={}, msg="报案区县不能为空")
    if not accident_type:
        return make_response(500, data={}, msg="事故类型不能为空")
    if not injury_type:
        return make_response(500, data={}, msg="伤情类型不能为空")
    if not insurance_company:
        return make_response(500, data={}, msg="所属保险公司不能为空")

    dup_stmt = (
        select(CaseRecord.id)
        .where(CaseRecord.report_number == report_number, CaseRecord.is_delete == 0)
        .limit(1)
    )
    if (await db.scalars(dup_stmt)).first() is not None:
        return make_response(500, data={}, msg="出险报案号已存在")

    now = datetime.utcnow()
    db.add(
        CaseRecord(
            report_number=report_number,
            victim_name=victim_name,
            victim_phone=victim_phone,
            report_date=body.reportDate,
            province=province,
            city=city,
            district=district,
            accident_type=accident_type,
            injury_type=injury_type,
            insurance_company=insurance_company,
            status=body.status,
            agency_id=body.agencyId,
            dept_id=ctx_dept_id.get(),
            created_by=ctx_user_id.get(),
            created_at=now,
            updated_at=now,
        )
    )
    await db.commit()
    return make_response(200, data={}, msg="新增成功")


@router.put("/{case_id}", dependencies=[Depends(require_permission("case:edit"))])
async def case_update(
    case_id: Union[str, int],
    body: CaseRecordUpdate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_case_id(case_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="案件 ID 无效")

    stmt = select(CaseRecord).where(CaseRecord.id == parsed_id, CaseRecord.is_delete == 0)
    stmt = apply_data_scope(stmt, CaseRecord)
    row = (await db.scalars(stmt)).first()
    if row is None:
        return make_response(500, data={}, msg="案件不存在或无权访问")

    if body.status is not None and body.status not in VALID_CASE_STATUS:
        return make_response(500, data={}, msg="案件状态参数无效")

    if body.reportNumber is not None:
        report_number = body.reportNumber.strip()
        if not report_number:
            return make_response(500, data={}, msg="出险报案号不能为空")
        dup_stmt = (
            select(CaseRecord.id)
            .where(
                CaseRecord.report_number == report_number,
                CaseRecord.is_delete == 0,
                CaseRecord.id != parsed_id,
            )
            .limit(1)
        )
        if (await db.scalars(dup_stmt)).first() is not None:
            return make_response(500, data={}, msg="出险报案号已存在")
        row.report_number = report_number

    if body.victimName is not None:
        victim_name = body.victimName.strip()
        if not victim_name:
            return make_response(500, data={}, msg="伤者姓名不能为空")
        row.victim_name = victim_name

    if body.victimPhone is not None:
        victim_phone = body.victimPhone.strip()
        if not victim_phone:
            return make_response(500, data={}, msg="联系电话不能为空")
        row.victim_phone = victim_phone

    if body.reportDate is not None:
        row.report_date = body.reportDate

    if body.province is not None:
        province = body.province.strip()
        if not province:
            return make_response(500, data={}, msg="报案省份不能为空")
        row.province = province

    if body.city is not None:
        city = body.city.strip()
        if not city:
            return make_response(500, data={}, msg="报案城市不能为空")
        row.city = city

    if body.district is not None:
        district = body.district.strip()
        if not district:
            return make_response(500, data={}, msg="报案区县不能为空")
        row.district = district

    if body.accidentType is not None:
        accident_type = body.accidentType.strip()
        if not accident_type:
            return make_response(500, data={}, msg="事故类型不能为空")
        row.accident_type = accident_type

    if body.injuryType is not None:
        injury_type = body.injuryType.strip()
        if not injury_type:
            return make_response(500, data={}, msg="伤情类型不能为空")
        row.injury_type = injury_type

    if body.insuranceCompany is not None:
        insurance_company = body.insuranceCompany.strip()
        if not insurance_company:
            return make_response(500, data={}, msg="所属保险公司不能为空")
        row.insurance_company = insurance_company

    if body.status is not None:
        row.status = body.status
    if body.agencyId is not None:
        row.agency_id = body.agencyId

    row.updated_at = datetime.utcnow()
    await db.commit()
    return make_response(200, data={}, msg="修改成功")


@router.delete("/{case_id}", dependencies=[Depends(require_permission("case:delete"))])
async def case_delete(
    case_id: Union[str, int],
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_case_id(case_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="案件 ID 无效")

    stmt = select(CaseRecord).where(CaseRecord.id == parsed_id, CaseRecord.is_delete == 0)
    stmt = apply_data_scope(stmt, CaseRecord)
    row = (await db.scalars(stmt)).first()
    if row is None:
        return make_response(500, data={}, msg="案件不存在或无权访问")

    row.is_delete = 1
    row.delete_time = datetime.utcnow()
    row.updated_at = datetime.utcnow()
    await db.commit()
    return make_response(200, data={}, msg="删除成功")
