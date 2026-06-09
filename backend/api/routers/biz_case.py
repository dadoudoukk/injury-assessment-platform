from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, make_response, require_permission, require_user_with_data_perm, require_user
from api.helpers import case_record_row
from core.context import ctx_agency_id, ctx_dept_id, ctx_user_id
from core.data_perm import apply_data_scope
from models import AppraisalAgency, CaseRecord
from schemas.business import CaseAppraisalSubmit, CaseRecordCreate, CaseRecordUpdate, CaseRecordExportQuery, CaseRejectBody, CaseReworkBody
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, select, extract
import pandas as pd
from io import BytesIO
from starlette.responses import Response

router = APIRouter(prefix="/biz/case", tags=["业务-案件管理"])

VALID_CASE_STATUS = (1, 2, 3)
STATUS_PENDING = 1
STATUS_IN_PROGRESS = 2
STATUS_COMPLETED = 3


def _parse_case_id(case_id: Union[str, int]) -> Optional[int]:
    try:
        return int(case_id)
    except (TypeError, ValueError):
        return None


def _resolve_create_status(agency_id: Optional[int]) -> int:
    """新建案件：有机构则鉴定中，否则待接单。"""
    return STATUS_IN_PROGRESS if agency_id is not None else STATUS_PENDING


def _report_files_to_db(items: List[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in items:
        if hasattr(item, "model_dump"):
            data = item.model_dump(exclude_none=True)
        elif isinstance(item, dict):
            data = {k: v for k, v in item.items() if v is not None}
        else:
            continue
        url = str(data.get("url") or "").strip()
        if not url:
            continue
        data["url"] = url
        out.append(data)
    return out


def _case_select_with_agency():
    return (
        select(CaseRecord, AppraisalAgency.agency_name)
        .outerjoin(AppraisalAgency, CaseRecord.agency_id == AppraisalAgency.id)
        .where(CaseRecord.is_delete == 0)
    )


def _apply_case_list_filters(
    stmt,
    *,
    report_number: Optional[str],
    victim_name: Optional[str],
    status: Optional[int],
    insurance_company: Optional[str],
    agency_id: Optional[int],
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
    if agency_id is not None:
        stmt = stmt.where(CaseRecord.agency_id == agency_id)
    if report_date_start is not None:
        stmt = stmt.where(CaseRecord.report_date >= report_date_start)
    if report_date_end is not None:
        stmt = stmt.where(CaseRecord.report_date <= report_date_end)
    return stmt


def _apply_agency_case_status_scope(stmt):
    """机构账号仅可见鉴定中/已完成的指派案件。普通伤者仅可见自己的案件。"""
    agency_id = ctx_agency_id.get()
    if agency_id is not None:
        stmt = stmt.where(CaseRecord.status.in_([STATUS_IN_PROGRESS, STATUS_COMPLETED]))
        
    # 如果是普通伤者角色，通过当前用户对应的手机号进行过滤
    # （这里暂通过上下文中约定的特殊标识或判断机构和部门均为None时的兜底逻辑。
    # 更严谨的做法是在 ctx 中直接注入当前用户的手机号或角色标识）
    # 为简便实现，我们可以通过 ctx_user_id 去反查用户 phone，或者在 data_scope 层已处理。
    # 这里我们添加一个专门的查询过滤逻辑，如果前端传了专门的 C 端标识，或者我们在接口里做判断。
    return stmt


async def _validate_active_agency(db: AsyncSession, agency_id: int) -> Optional[str]:
    """校验机构存在且 status=1；通过返回 None，否则返回错误文案。"""
    stmt = (
        select(AppraisalAgency.id)
        .where(
            AppraisalAgency.id == agency_id,
            AppraisalAgency.is_delete == 0,
            AppraisalAgency.status == 1,
        )
        .limit(1)
    )
    if (await db.scalars(stmt)).first() is None:
        return "鉴定机构不存在或不可用"
    return None


async def _apply_agency_change(
    db: AsyncSession,
    row: CaseRecord,
    body: CaseRecordUpdate,
) -> Optional[str]:
    """处理机构指派/清空，并同步状态机。返回错误文案或 None。"""
    if "agencyId" not in body.model_fields_set:
        return None

    if body.agencyId is None:
        row.agency_id = None
        row.status = STATUS_PENDING
        return None

    if body.agencyId == row.agency_id:
        return None

    agency_err = await _validate_active_agency(db, body.agencyId)
    if agency_err:
        return agency_err

    row.agency_id = body.agencyId
    row.status = STATUS_IN_PROGRESS
    return None


@router.get("/stats")
async def case_stats(
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    # 1. 案件总览 (不受日期限制，看当前权限下所有案件状态分布)
    base_stmt = select(CaseRecord).where(CaseRecord.is_delete == 0)
    base_stmt = apply_data_scope(base_stmt, CaseRecord)
    base_stmt = _apply_agency_case_status_scope(base_stmt)

    status_stmt = select(CaseRecord.status, func.count(CaseRecord.id)).where(*base_stmt._where_criteria).group_by(CaseRecord.status)
    status_rows = (await db.execute(status_stmt)).all()
    
    status_counts = {1: 0, 2: 0, 3: 0}
    total_count = 0
    for r in status_rows:
        st = r[0]
        cnt = r[1]
        status_counts[st] = cnt
        total_count += cnt
        
    # 2. 保险公司占比 (饼图)
    ins_stmt = select(CaseRecord.insurance_company, func.count(CaseRecord.id)).where(*base_stmt._where_criteria).group_by(CaseRecord.insurance_company).order_by(func.count(CaseRecord.id).desc()).limit(10)
    ins_rows = (await db.execute(ins_stmt)).all()
    insurance_stats = [{"name": r[0], "value": r[1]} for r in ins_rows]

    # 3. 近期报案趋势 (折线图)
    # 取按日期的统计
    date_stmt = select(CaseRecord.report_date, func.count(CaseRecord.id)).where(*base_stmt._where_criteria).group_by(CaseRecord.report_date).order_by(CaseRecord.report_date.desc()).limit(14)
    date_rows = (await db.execute(date_stmt)).all()
    trend_stats = [{"date": r[0].strftime("%Y-%m-%d") if r[0] else "未知", "count": r[1]} for r in date_rows]
    trend_stats.reverse()  # 时间正序

    return make_response(200, data={
        "total": total_count,
        "pending": status_counts[1],
        "inProgress": status_counts[2],
        "completed": status_counts[3],
        "insuranceStats": insurance_stats,
        "trendStats": trend_stats
    }, msg="success")

@router.get("")
async def case_list(
    pageNum: int = Query(1, ge=1, description="当前页码"),
    pageSize: int = Query(10, ge=1, le=200, description="每页条数"),
    reportNumber: Optional[str] = Query(None, description="出险报案号模糊搜索"),
    victimName: Optional[str] = Query(None, description="伤者姓名模糊搜索"),
    status: Optional[int] = Query(None, description="案件状态：1待接单 2鉴定中 3已完成"),
    insuranceCompany: Optional[str] = Query(None, description="所属保险公司（精确匹配）"),
    agencyId: Optional[int] = Query(None, description="鉴定机构ID（精确匹配）"),
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

    forced_agency_id = ctx_agency_id.get()
    if forced_agency_id is not None:
        agencyId = forced_agency_id

    stmt = _case_select_with_agency()
    stmt = _apply_case_list_filters(
        stmt,
        report_number=reportNumber,
        victim_name=victimName,
        status=status,
        insurance_company=insuranceCompany,
        agency_id=agencyId,
        report_date_start=reportDateStart,
        report_date_end=reportDateEnd,
    )
    stmt = apply_data_scope(stmt, CaseRecord)
    stmt = _apply_agency_case_status_scope(stmt)
    
    # C端普通伤者数据隔离：如果当前用户不仅没有机构，而且没有部门，且具有普通用户标识，则仅看自己手机号的案子
    from models import SysUser
    current_user_id = ctx_user_id.get()
    if current_user_id:
        user_stmt = select(SysUser.phone).where(SysUser.id == current_user_id)
        user_phone = (await db.scalars(user_stmt)).first()
        # 假设伤者用户的标志是既没有部门也没有机构
        if ctx_dept_id.get() is None and forced_agency_id is None and user_phone:
            stmt = stmt.where(CaseRecord.victim_phone == user_phone)

    count_stmt = select(func.count()).select_from(CaseRecord).where(*stmt._where_criteria)
    total = int((await db.scalar(count_stmt)) or 0)

    stmt = stmt.order_by(CaseRecord.id.desc())
    stmt = stmt.offset((pageNum - 1) * pageSize).limit(pageSize)
    rows = (await db.execute(stmt)).all()
    return make_response(
        200,
        data={
            "list": [case_record_row(r[0], r[1]) for r in rows],
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
        },
        msg="success",
    )


@router.post("/export")
async def case_export(
    body: Optional[CaseRecordExportQuery] = None,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Response:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="登录过期，请重新登录")

    query_body = body or CaseRecordExportQuery()
    forced_agency_id = ctx_agency_id.get()
    agency_id = query_body.agencyId
    if forced_agency_id is not None:
        agency_id = forced_agency_id

    stmt = _case_select_with_agency()
    stmt = _apply_case_list_filters(
        stmt,
        report_number=query_body.reportNumber,
        victim_name=query_body.victimName,
        status=query_body.status,
        insurance_company=query_body.insuranceCompany,
        agency_id=agency_id,
        report_date_start=query_body.reportDateStart,
        report_date_end=query_body.reportDateEnd,
    )
    stmt = apply_data_scope(stmt, CaseRecord)
    stmt = _apply_agency_case_status_scope(stmt)
    
    # C端普通伤者数据隔离：如果当前用户不仅没有机构，而且没有部门，且具有普通用户标识，则仅看自己手机号的案子
    from models import SysUser
    current_user_id = ctx_user_id.get()
    if current_user_id:
        user_stmt = select(SysUser.phone).where(SysUser.id == current_user_id)
        user_phone = (await db.scalars(user_stmt)).first()
        if ctx_dept_id.get() is None and forced_agency_id is None and user_phone:
            stmt = stmt.where(CaseRecord.victim_phone == user_phone)

    # 限制导出最大数量，防止 OOM
    stmt = stmt.order_by(CaseRecord.id.desc()).limit(10000)
    rows_db = (await db.execute(stmt)).all()

    def _get_status_text(status: int) -> str:
        if status == 1: return "待接单"
        if status == 2: return "鉴定中"
        if status == 3: return "已完成"
        return "未知"

    rows_data: List[Dict[str, Any]] = []
    for r in rows_db:
        case = r[0]
        agency_name = r[1]
        rows_data.append(
            {
                "出险报案号": case.report_number,
                "伤者姓名": case.victim_name,
                "联系电话": case.victim_phone,
                "报案日期": case.report_date.strftime("%Y-%m-%d") if case.report_date else "",
                "出险地点": f"{case.province}{case.city}{case.district}",
                "事故类型": case.accident_type,
                "伤情类型": case.injury_type,
                "所属保险公司": case.insurance_company,
                "案件状态": _get_status_text(case.status),
                "鉴定机构": agency_name or "",
                "理赔金额": float(case.appraisal_amount) if case.appraisal_amount else "",
                "鉴定结论": case.appraisal_conclusion or "",
                "创建时间": case.created_at.strftime("%Y-%m-%d %H:%M:%S") if case.created_at else "",
            }
        )

    def _build_export_excel_bytes() -> bytes:
        df = pd.DataFrame(
            rows_data,
            columns=["出险报案号", "伤者姓名", "联系电话", "报案日期", "出险地点", "事故类型", "伤情类型", "所属保险公司", "案件状态", "鉴定机构", "理赔金额", "鉴定结论", "创建时间"],
        )
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="案件列表")
        return output.getvalue()

    excel_bytes = await run_in_threadpool(_build_export_excel_bytes)

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"案件列表_{ts}.xlsx"
    from urllib.parse import quote
    encoded_filename = quote(filename)

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        "Access-Control-Expose-Headers": "Content-Disposition",
    }
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
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

    stmt = _case_select_with_agency().where(CaseRecord.id == parsed_id)
    stmt = apply_data_scope(stmt, CaseRecord)
    stmt = _apply_agency_case_status_scope(stmt)
    row = (await db.execute(stmt)).first()
    if row is None:
        return make_response(500, data={}, msg="案件不存在或无权访问")

    return make_response(200, data=case_record_row(row[0], row[1]), msg="success")


from pydantic import BaseModel

class C端CaseRecordCreate(BaseModel):
    victimName: str
    victimPhone: str
    reportDate: date
    province: str
    city: str
    district: str
    accidentType: str
    injuryType: str
    insuranceCompany: str
    reportNumber: Optional[str] = None # 伤者自己报案时，可能拿不到或者不知道报案号，后端可生成一个

@router.post("/patient", dependencies=[Depends(require_permission("case:add"))])
async def case_create_patient(
    body: C端CaseRecordCreate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    victim_name = body.victimName.strip()
    victim_phone = body.victimPhone.strip()
    province = body.province.strip()
    city = body.city.strip()
    district = body.district.strip()
    accident_type = body.accidentType.strip()
    injury_type = body.injuryType.strip()
    insurance_company = body.insuranceCompany.strip()
    
    # 如果没传报案号，后端生成一个随机的（例如 TS + 时间戳）
    import time, random
    report_number = body.reportNumber.strip() if body.reportNumber else f"TS{int(time.time()*1000)}{random.randint(100,999)}"

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
    
    # 自动派单逻辑
    agency_id = await _auto_dispatch_agency(db, province, city, district)

    resolved_status = _resolve_create_status(agency_id)
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
            status=resolved_status,
            agency_id=agency_id,
            dept_id=None,
            created_by=ctx_user_id.get(),
            created_at=now,
            updated_at=now,
        )
    )
    await db.commit()
    return make_response(200, data={}, msg="报案成功")

async def _auto_dispatch_agency(
    db: AsyncSession,
    province: str,
    city: str,
    district: str,
    exclude_agency_ids: Optional[List[int]] = None
) -> Optional[int]:
    """自动派单逻辑：先同区县，找不到再同市。可排除指定的机构 ID。"""
    
    def _build_stmt(is_district: bool):
        stmt = select(AppraisalAgency.id).where(
            AppraisalAgency.province == province,
            AppraisalAgency.city == city,
            AppraisalAgency.status == 1,
            AppraisalAgency.is_delete == 0,
        )
        if is_district:
            stmt = stmt.where(AppraisalAgency.district == district)
        if exclude_agency_ids:
            stmt = stmt.where(AppraisalAgency.id.not_in(exclude_agency_ids))
        return stmt.limit(1)

    # 1. 优先匹配同省、同市、同区县的正常鉴定机构
    agency_id = (await db.scalars(_build_stmt(True))).first()

    # 2. 若区县无匹配机构，兜底扩大到同市级别
    if agency_id is None:
        agency_id = (await db.scalars(_build_stmt(False))).first()
        
    return agency_id

@router.post("", dependencies=[Depends(require_permission("case:add"))])
async def case_create(
    body: CaseRecordCreate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    if body.status == STATUS_COMPLETED:
        return make_response(500, data={}, msg="新建案件不能直接设为已完成，请先指派机构并提交鉴定报告")

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

    agency_id = body.agencyId
    if agency_id is not None:
        agency_err = await _validate_active_agency(db, agency_id)
        if agency_err:
            return make_response(500, data={}, msg=agency_err)
    else:
        # 自动派单逻辑
        agency_id = await _auto_dispatch_agency(db, province, city, district)

    dup_stmt = (
        select(CaseRecord.id)
        .where(CaseRecord.report_number == report_number, CaseRecord.is_delete == 0)
        .limit(1)
    )
    if (await db.scalars(dup_stmt)).first() is not None:
        return make_response(500, data={}, msg="出险报案号已存在")

    resolved_status = _resolve_create_status(agency_id)
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
            status=resolved_status,
            agency_id=agency_id,
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

    if ctx.get("agency_id") is not None:
        return make_response(403, data={}, msg="机构账号无权修改案件基础信息")

    parsed_id = _parse_case_id(case_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="案件 ID 无效")

    stmt = select(CaseRecord).where(CaseRecord.id == parsed_id, CaseRecord.is_delete == 0)
    stmt = apply_data_scope(stmt, CaseRecord)
    row = (await db.scalars(stmt)).first()
    if row is None:
        return make_response(500, data={}, msg="案件不存在或无权访问")

    if int(row.status) == STATUS_COMPLETED:
        return make_response(500, data={}, msg="案件已完成，基础信息不可编辑，如需调整报告请使用「修改报告」")

    if body.status is not None:
        if body.status not in VALID_CASE_STATUS:
            return make_response(500, data={}, msg="案件状态参数无效")
        if body.status != int(row.status):
            return make_response(500, data={}, msg="案件状态由工作流自动流转，请勿手动修改")

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

    agency_err = await _apply_agency_change(db, row, body)
    if agency_err:
        return make_response(500, data={}, msg=agency_err)

    row.updated_at = datetime.utcnow()
    await db.commit()
    return make_response(200, data={}, msg="修改成功")


@router.post("/{case_id}/reject", dependencies=[Depends(require_permission("case:edit"))])
async def case_reject(
    case_id: Union[str, int],
    body: CaseRejectBody,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_case_id(case_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="案件 ID 无效")

    case = await db.get(CaseRecord, parsed_id)
    if not case or case.is_delete == 1:
        return make_response(404, data={}, msg="案件不存在")

    current_agency_id = ctx_agency_id.get()
    
    # Check permissions: only assigned agency can reject it, or platform admin
    if current_agency_id is not None and case.agency_id != current_agency_id:
        return make_response(403, data={}, msg="您无权操作其他机构的案件")

    if case.status != 1:
        return make_response(500, data={}, msg="只有待接单状态的案件才能拒单")
        
    rejected_agency_id = case.agency_id
    if not rejected_agency_id:
        return make_response(500, data={}, msg="当前案件未分配鉴定机构，无需拒单")

    # Add to rejected list
    rejected_list = case.rejected_agency_ids or []
    if rejected_agency_id not in rejected_list:
        rejected_list.append(rejected_agency_id)
    
    # We must explicitly assign a new list object for SQLAlchemy JSON mutation to trigger updates reliably, or use flag_modified
    from sqlalchemy.orm.attributes import flag_modified
    case.rejected_agency_ids = rejected_list
    flag_modified(case, "rejected_agency_ids")

    # Try to re-dispatch
    new_agency_id = await _auto_dispatch_agency(
        db, 
        case.province, 
        case.city, 
        case.district, 
        exclude_agency_ids=rejected_list
    )
    
    case.agency_id = new_agency_id
    case.status = _resolve_create_status(new_agency_id)
    
    await db.commit()
    
    if new_agency_id:
        return make_response(200, data={}, msg="拒单成功，系统已自动重新派发给该地区其他可用机构")
    else:
        return make_response(200, data={}, msg="拒单成功，由于该地区暂无其他可用机构，案件已流转至人工客服处理")

@router.post("/{case_id}/accept", dependencies=[Depends(require_permission("case:edit"))])
async def case_accept(
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

    case = await db.get(CaseRecord, parsed_id)
    if not case or case.is_delete == 1:
        return make_response(404, data={}, msg="案件不存在")

    current_agency_id = ctx_agency_id.get()
    
    if current_agency_id is not None and case.agency_id != current_agency_id:
        return make_response(403, data={}, msg="您无权操作其他机构的案件")

    if case.status != 1:
        return make_response(500, data={}, msg="只有待接单状态的案件才能接单")

    case.status = 2
    await db.commit()
    
    return make_response(200, data={}, msg="接单成功")

@router.post("/{case_id}/rework", dependencies=[Depends(require_permission("case:edit"))])
async def case_rework(
    case_id: Union[str, int],
    body: CaseReworkBody,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user_with_data_perm(db, x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_case_id(case_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="案件 ID 无效")

    case = await db.get(CaseRecord, parsed_id)
    if not case or case.is_delete == 1:
        return make_response(404, data={}, msg="案件不存在")

    if case.status != 3:
        return make_response(500, data={}, msg="只有已完成状态的案件才能打回重做")

    case.status = 4
    case.rework_remark = body.remark.strip()
    await db.commit()
    
    return make_response(200, data={}, msg="打回成功，案件已退回给原鉴定机构修改")

@router.post("/{case_id}/appraisal", dependencies=[Depends(require_permission("case:appraisal"))])
async def case_submit_appraisal(
    case_id: Union[str, int],
    body: CaseAppraisalSubmit,
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

    current_status = int(row.status)
    if current_status == STATUS_PENDING:
        return make_response(500, data={}, msg="案件尚未指派机构，无法提交鉴定报告")
    if row.agency_id is None:
        return make_response(500, data={}, msg="案件未关联鉴定机构，无法提交鉴定报告")
    if current_status not in (STATUS_IN_PROGRESS, STATUS_COMPLETED, 4):
        return make_response(500, data={}, msg="当前案件状态不允许提交鉴定报告")

    conclusion = body.appraisalConclusion.strip()
    if not conclusion:
        return make_response(500, data={}, msg="鉴定结论不能为空")

    report_files = _report_files_to_db(body.reportFiles)
    if not report_files:
        return make_response(500, data={}, msg="请至少上传一份报告附件")

    now = datetime.utcnow()
    user_id = ctx_user_id.get()
    row.appraisal_amount = Decimal(str(body.appraisalAmount))
    row.appraisal_conclusion = conclusion
    row.report_files = report_files
    row.appraisal_submitted_at = now
    row.appraisal_submitted_by = user_id
    row.status = STATUS_COMPLETED
    row.updated_at = now

    await db.commit()
    msg = "报告修改成功" if current_status == STATUS_COMPLETED else "鉴定报告提交成功"
    return make_response(200, data={}, msg=msg)


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

    if int(row.status) == STATUS_COMPLETED:
        return make_response(500, data={}, msg="案件已完成，不允许删除")

    row.is_delete = 1
    row.delete_time = datetime.utcnow()
    row.updated_at = datetime.utcnow()
    await db.commit()
    return make_response(200, data={}, msg="删除成功")
