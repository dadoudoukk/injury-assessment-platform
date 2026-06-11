from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.concurrency import run_in_threadpool
import pandas as pd
from io import BytesIO
from starlette.responses import Response

from api.deps import get_async_db, make_response, require_permission, require_user_with_data_perm
from api.helpers import case_record_row
from core.context import ctx_agency_id, ctx_dept_id, ctx_user_id
from core.data_perm import apply_data_scope
from core.file_validate import MAX_VIDEO_COUNT, validate_video_upload
from core.paths import UPLOAD_DIR
from core.region import city_equivalent_values, normalize_region
from models import AppraisalAgency, BizInsuranceCompany, CaseRecord, SysUser
from schemas.business import (
    CaseAppraisalVideosSubmit,
    CaseDocumentNumberSubmit,
    CaseRecordCreate,
    CaseRecordExportQuery,
    CaseRecordUpdate,
    CaseReworkBody,
)

router = APIRouter(prefix="/biz/case", tags=["业务-案件管理"])

STATUS_PENDING_CONFIRM = 1
STATUS_ACCEPTED = 2
STATUS_APPRAISING = 3
STATUS_COMPLETED = 4
STATUS_REWORK = 5

VALID_CASE_STATUS = (1, 2, 3, 4, 5)
CASE_STATUS_LABELS = {
    STATUS_PENDING_CONFIRM: "待确认",
    STATUS_ACCEPTED: "已受理",
    STATUS_APPRAISING: "鉴定中",
    STATUS_COMPLETED: "已完成",
    STATUS_REWORK: "已打回",
}


def _parse_case_id(case_id: Union[str, int]) -> Optional[int]:
    try:
        return int(case_id)
    except (TypeError, ValueError):
        return None


def _resolve_create_status(agency_id: Optional[int]) -> int:
    """新建/派单：有机构则待确认，否则仍为待确认（待平台派单）。"""
    return STATUS_PENDING_CONFIRM


async def _notify_agency_case_event(case: CaseRecord, event: str) -> None:
    """TODO: 小程序订阅消息或短信通知鉴定机构（event: assigned / rework）。"""
    _ = case, event


async def _ensure_report_number_available(
    db: AsyncSession,
    report_number: str,
    exclude_id: Optional[int] = None,
) -> Optional[str]:
    """校验未删除案件中报案号是否重复，返回错误信息或 None。"""
    stmt = select(CaseRecord.id).where(
        CaseRecord.report_number == report_number,
        CaseRecord.is_delete == 0,
    )
    if exclude_id is not None:
        stmt = stmt.where(CaseRecord.id != exclude_id)
    if (await db.scalars(stmt.limit(1))).first() is not None:
        return "出险报案号已存在"
    return None


def _release_report_number(report_number: str, case_id: int, deleted_at: datetime) -> str:
    """软删除时释放报案号，避免历史唯一索引占用。"""
    suffix = f"__del{case_id}_{int(deleted_at.timestamp())}"
    max_base = max(50 - len(suffix), 1)
    return f"{report_number[:max_base]}{suffix}"


def _media_items_to_db(items: List[Any]) -> List[Dict[str, Any]]:
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


def _upload_basename_from_url(url: str) -> Optional[str]:
    path = urlparse(url).path.strip("/")
    if not path:
        return None
    name = path.split("/")[-1].strip()
    return name or None


def _validate_stored_videos(video_items: List[Dict[str, Any]]) -> Optional[str]:
    if not video_items:
        return "请至少上传一个鉴定视频"
    if len(video_items) > MAX_VIDEO_COUNT:
        return f"鉴定视频最多 {MAX_VIDEO_COUNT} 个"
    for item in video_items:
        url = str(item.get("url") or "").strip()
        basename = _upload_basename_from_url(url)
        if not basename:
            return "视频地址无效"
        path = UPLOAD_DIR / basename
        if not path.is_file():
            return "视频文件不存在或已失效，请重新上传"
        err = validate_video_upload(path, path.stat().st_size)
        if err:
            return err
    return None


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
        stmt = stmt.where(CaseRecord.insurance_company.like(f"%{insurance_company.strip()}%"))
    if agency_id is not None:
        stmt = stmt.where(CaseRecord.agency_id == agency_id)
    if report_date_start is not None:
        stmt = stmt.where(CaseRecord.report_date >= report_date_start)
    if report_date_end is not None:
        stmt = stmt.where(CaseRecord.report_date <= report_date_end)
    return stmt


def _apply_agency_case_status_scope(stmt):
    """机构账号可见其指派案件的全部流转状态（1~5）。"""
    return stmt


def _apply_case_list_order(stmt, *, is_agency: bool, status_filter: Optional[int]):
    if not is_agency:
        return stmt.order_by(CaseRecord.id.desc())
    if status_filter == STATUS_PENDING_CONFIRM:
        return stmt.order_by(CaseRecord.created_at.desc())
    if status_filter is not None:
        return stmt.order_by(CaseRecord.updated_at.desc())
    pending_first = case((CaseRecord.status == STATUS_PENDING_CONFIRM, 0), else_=1)
    sort_time = case(
        (CaseRecord.status == STATUS_PENDING_CONFIRM, CaseRecord.created_at),
        else_=CaseRecord.updated_at,
    )
    return stmt.order_by(pending_first.asc(), sort_time.desc())


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
        row.status = STATUS_PENDING_CONFIRM
        return None

    if body.agencyId == row.agency_id:
        return None

    agency_err = await _validate_active_agency(db, body.agencyId)
    if agency_err:
        return agency_err

    row.agency_id = body.agencyId
    row.status = STATUS_PENDING_CONFIRM
    await _notify_agency_case_event(row, "assigned")
    return None


def _build_case_activity(row: CaseRecord, agency_name: Optional[str]) -> Dict[str, Any]:
    """根据案件当前状态生成首页时间轴文案。"""
    agency_label = agency_name or "鉴定机构"
    report_no = row.report_number
    if int(row.status) == STATUS_COMPLETED:
        content = f"案件 {report_no} 由 [{agency_label}] 完成鉴定，出具报告"
        activity_type = "success"
    elif int(row.status) == STATUS_PENDING_CONFIRM:
        content = f"新增报案：{row.victim_name} 提交了{row.accident_type}人伤鉴定申请"
        activity_type = "primary"
    elif int(row.status) == STATUS_ACCEPTED:
        content = f"案件 {report_no} 已由 [{agency_label}] 确认受理"
        activity_type = "warning"
    elif int(row.status) == STATUS_APPRAISING:
        content = f"案件 {report_no} 已由 [{agency_label}] 提交鉴定视频，鉴定中"
        activity_type = "warning"
    elif int(row.status) == STATUS_REWORK:
        remark = (row.rework_remark or "待补充材料").strip()
        content = f"案件 {report_no} 被保险公司打回：{remark}"
        activity_type = "danger"
    else:
        content = f"案件 {report_no} 状态更新为 {CASE_STATUS_LABELS.get(int(row.status), '未知')}"
        activity_type = "info"

    return {
        "content": content,
        "timestamp": row.updated_at.strftime("%Y-%m-%d %H:%M") if row.updated_at else "",
        "type": activity_type,
    }


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
    where_criteria = list(base_stmt._where_criteria)

    status_stmt = select(CaseRecord.status, func.count(CaseRecord.id)).where(*where_criteria).group_by(CaseRecord.status)
    status_rows = (await db.execute(status_stmt)).all()

    status_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_count = 0
    for r in status_rows:
        st = int(r[0])
        cnt = int(r[1])
        if st in status_counts:
            status_counts[st] = cnt
        total_count += cnt

    status_stats = [
        {"name": CASE_STATUS_LABELS[STATUS_PENDING_CONFIRM], "value": status_counts[STATUS_PENDING_CONFIRM]},
        {"name": CASE_STATUS_LABELS[STATUS_ACCEPTED], "value": status_counts[STATUS_ACCEPTED]},
        {"name": CASE_STATUS_LABELS[STATUS_APPRAISING], "value": status_counts[STATUS_APPRAISING]},
        {"name": CASE_STATUS_LABELS[STATUS_COMPLETED], "value": status_counts[STATUS_COMPLETED]},
        {"name": CASE_STATUS_LABELS[STATUS_REWORK], "value": status_counts[STATUS_REWORK]},
    ]

    # 2. 保险公司占比 (饼图，保留给数据大屏复用)
    ins_stmt = (
        select(CaseRecord.insurance_company, func.count(CaseRecord.id))
        .where(*where_criteria)
        .group_by(CaseRecord.insurance_company)
        .order_by(func.count(CaseRecord.id).desc())
        .limit(10)
    )
    ins_rows = (await db.execute(ins_stmt)).all()
    insurance_stats = [{"name": r[0] or "未知", "value": r[1]} for r in ins_rows]

    # 3. 近 30 天新增趋势（按创建时间）
    today = date.today()
    trend_start = today - timedelta(days=29)
    trend_stmt = (
        select(func.date(CaseRecord.created_at), func.count(CaseRecord.id))
        .where(*where_criteria, func.date(CaseRecord.created_at) >= trend_start)
        .group_by(func.date(CaseRecord.created_at))
    )
    trend_rows = (await db.execute(trend_stmt)).all()
    trend_map = {r[0]: int(r[1]) for r in trend_rows if r[0]}
    trend_stats = []
    for offset in range(30):
        day = trend_start + timedelta(days=offset)
        trend_stats.append(
            {
                "date": day.strftime("%m-%d"),
                "fullDate": day.strftime("%Y-%m-%d"),
                "count": trend_map.get(day, 0),
            }
        )

    # 4. 周环比（近 7 天 vs 前 7 天新增案件）
    week_start = today - timedelta(days=6)
    prev_week_start = today - timedelta(days=13)
    prev_week_end = today - timedelta(days=7)
    current_week_count = int(
        (
            await db.scalar(
                select(func.count(CaseRecord.id)).where(
                    *where_criteria,
                    func.date(CaseRecord.created_at) >= week_start,
                    func.date(CaseRecord.created_at) <= today,
                )
            )
        )
        or 0
    )
    previous_week_count = int(
        (
            await db.scalar(
                select(func.count(CaseRecord.id)).where(
                    *where_criteria,
                    func.date(CaseRecord.created_at) >= prev_week_start,
                    func.date(CaseRecord.created_at) <= prev_week_end,
                )
            )
        )
        or 0
    )
    if previous_week_count > 0:
        week_growth = round((current_week_count - previous_week_count) / previous_week_count * 100, 1)
    elif current_week_count > 0:
        week_growth = 100.0
    else:
        week_growth = 0.0

    # 5. 平台规模（全平台统计，不受案件数据权限影响）
    agency_count = int(
        (
            await db.scalar(
                select(func.count(AppraisalAgency.id)).where(
                    AppraisalAgency.is_delete == 0,
                    AppraisalAgency.status == 1,
                )
            )
        )
        or 0
    )
    insurance_count = int(
        (
            await db.scalar(
                select(func.count(BizInsuranceCompany.id)).where(
                    BizInsuranceCompany.is_delete == 0,
                    BizInsuranceCompany.status == 1,
                )
            )
        )
        or 0
    )

    # 6. 最新案件流转动态
    recent_stmt = _case_select_with_agency().where(*where_criteria).order_by(CaseRecord.updated_at.desc()).limit(8)
    recent_rows = (await db.execute(recent_stmt)).all()
    recent_activities = [_build_case_activity(row, agency_name) for row, agency_name in recent_rows]

    return make_response(
        200,
        data={
            "total": total_count,
            "pending": status_counts[STATUS_PENDING_CONFIRM],
            "accepted": status_counts[STATUS_ACCEPTED],
            "inProgress": status_counts[STATUS_APPRAISING],
            "completed": status_counts[STATUS_COMPLETED],
            "rework": status_counts[STATUS_REWORK],
            "agencyCount": agency_count,
            "insuranceCount": insurance_count,
            "weekGrowth": week_growth,
            "statusStats": status_stats,
            "insuranceStats": insurance_stats,
            "trendStats": trend_stats,
            "recentActivities": recent_activities,
        },
        msg="success",
    )

@router.get("")
async def case_list(
    pageNum: int = Query(1, ge=1, description="当前页码"),
    pageSize: int = Query(10, ge=1, le=200, description="每页条数"),
    reportNumber: Optional[str] = Query(None, description="出险报案号模糊搜索"),
    victimName: Optional[str] = Query(None, description="伤者姓名模糊搜索"),
    status: Optional[int] = Query(None, description="案件状态：1待确认 2已受理 3鉴定中 4已完成 5已打回"),
    insuranceCompany: Optional[str] = Query(None, description="所属保险公司（模糊搜索）"),
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
    
    # C端普通伤者数据隔离
    current_user_id = ctx_user_id.get()
    if current_user_id:
        user_stmt = select(SysUser.phone).where(SysUser.id == current_user_id)
        user_phone = (await db.scalars(user_stmt)).first()
        if ctx_dept_id.get() is None and forced_agency_id is None and user_phone:
            stmt = stmt.where(
                or_(
                    CaseRecord.victim_phone == user_phone,
                    CaseRecord.created_by == current_user_id,
                )
            )

    count_stmt = select(func.count()).select_from(CaseRecord).where(*stmt._where_criteria)
    total = int((await db.scalar(count_stmt)) or 0)

    stmt = _apply_case_list_order(stmt, is_agency=forced_agency_id is not None, status_filter=status)
    stmt = stmt.offset((pageNum - 1) * pageSize).limit(pageSize)
    rows = (await db.execute(stmt)).all()
    return make_response(
        200,
        data={
            "list": [case_record_row(r[0], r[1], ctx) for r in rows],
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
    
    # C端普通伤者数据隔离
    current_user_id = ctx_user_id.get()
    if current_user_id:
        user_stmt = select(SysUser.phone).where(SysUser.id == current_user_id)
        user_phone = (await db.scalars(user_stmt)).first()
        if ctx_dept_id.get() is None and forced_agency_id is None and user_phone:
            stmt = stmt.where(
                or_(
                    CaseRecord.victim_phone == user_phone,
                    CaseRecord.created_by == current_user_id,
                )
            )

    stmt = stmt.order_by(CaseRecord.id.desc()).limit(10000)
    rows_db = (await db.execute(stmt)).all()

    def _get_status_text(st: int) -> str:
        return CASE_STATUS_LABELS.get(int(st), "未知")

    rows_data: List[Dict[str, Any]] = []
    for r in rows_db:
        case = r[0]
        agency_name = r[1]
        row_data = case_record_row(case, agency_name, ctx)
        rows_data.append(
            {
                "出险报案号": case.report_number,
                "伤者姓名": row_data["victimName"],
                "联系电话": row_data["victimPhone"],
                "报案日期": case.report_date.strftime("%Y-%m-%d") if case.report_date else "",
                "出险地点": f"{case.province}{case.city}{case.district}",
                "事故类型": case.accident_type,
                "伤情类型": case.injury_type,
                "所属保险公司": case.insurance_company,
                "案件状态": _get_status_text(case.status),
                "鉴定机构": agency_name or "",
                "鉴定文书编号": case.document_number or "",
                "理赔金额": float(case.appraisal_amount) if case.appraisal_amount else "",
                "鉴定结论": case.appraisal_conclusion or "",
                "创建时间": case.created_at.strftime("%Y-%m-%d %H:%M:%S") if case.created_at else "",
            }
        )

    def _build_export_excel_bytes() -> bytes:
        df = pd.DataFrame(
            rows_data,
            columns=[
                "出险报案号", "伤者姓名", "联系电话", "报案日期", "出险地点", "事故类型", "伤情类型",
                "所属保险公司", "案件状态", "鉴定机构", "鉴定文书编号", "理赔金额", "鉴定结论", "创建时间",
            ],
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

    return make_response(200, data=case_record_row(row[0], row[1], ctx), msg="success")


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
    reportNumber: str

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
    report_number = body.reportNumber.strip()

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
    if not report_number:
        return make_response(500, data={}, msg="出险报案号不能为空")
    if not insurance_company:
        return make_response(500, data={}, msg="所属保险公司不能为空")

    province, city, district = normalize_region(province, city, district)

    # 自动派单逻辑
    agency_id = await _auto_dispatch_agency(db, province, city, district)

    dup_msg = await _ensure_report_number_available(db, report_number)
    if dup_msg:
        return make_response(500, data={}, msg=dup_msg)

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
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return make_response(500, data={}, msg="出险报案号已存在")
    return make_response(200, data={}, msg="报案成功")

async def _auto_dispatch_agency(
    db: AsyncSession,
    province: str,
    city: str,
    district: str,
) -> Optional[int]:
    """自动派单逻辑：先同区县，找不到再同市。"""
    province, city, district = normalize_region(province, city, district)
    city_variants = city_equivalent_values(province, city)

    def _build_stmt(is_district: bool):
        stmt = select(AppraisalAgency.id).where(
            AppraisalAgency.province == province,
            AppraisalAgency.city.in_(city_variants),
            AppraisalAgency.status == 1,
            AppraisalAgency.is_delete == 0,
        )
        if is_district:
            stmt = stmt.where(AppraisalAgency.district == district)
        return stmt.limit(1)

    agency_id = (await db.scalars(_build_stmt(True))).first()
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

    province, city, district = normalize_region(province, city, district)

    agency_id = body.agencyId
    if agency_id is not None:
        agency_err = await _validate_active_agency(db, agency_id)
        if agency_err:
            return make_response(500, data={}, msg=agency_err)
    else:
        # 自动派单逻辑
        agency_id = await _auto_dispatch_agency(db, province, city, district)

    dup_msg = await _ensure_report_number_available(db, report_number)
    if dup_msg:
        return make_response(500, data={}, msg=dup_msg)

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
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return make_response(500, data={}, msg="出险报案号已存在")
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
        return make_response(500, data={}, msg="案件已完成，基础信息不可编辑")

    if body.status is not None:
        if body.status not in VALID_CASE_STATUS:
            return make_response(500, data={}, msg="案件状态参数无效")
        if body.status != int(row.status):
            return make_response(500, data={}, msg="案件状态由工作流自动流转，请勿手动修改")

    if body.reportNumber is not None:
        report_number = body.reportNumber.strip()
        if not report_number:
            return make_response(500, data={}, msg="出险报案号不能为空")
        dup_msg = await _ensure_report_number_available(db, report_number, exclude_id=parsed_id)
        if dup_msg:
            return make_response(500, data={}, msg=dup_msg)
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

    if any(x is not None for x in (body.province, body.city, body.district)):
        row.province, row.city, row.district = normalize_region(row.province, row.city, row.district)

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


async def _ensure_agency_case_access(case: CaseRecord, ctx: Dict[str, Any]) -> Optional[str]:
    current_agency_id = ctx.get("agency_id")
    if current_agency_id is not None and case.agency_id != current_agency_id:
        return "您无权操作其他机构的案件"
    return None


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

    access_err = await _ensure_agency_case_access(case, ctx)
    if access_err:
        return make_response(403, data={}, msg=access_err)

    if int(case.status) != STATUS_PENDING_CONFIRM:
        return make_response(500, data={}, msg="只有待确认状态的案件才能确认受理")
    if case.agency_id is None:
        return make_response(500, data={}, msg="案件未分配鉴定机构，无法受理")

    case.status = STATUS_ACCEPTED
    case.updated_at = datetime.utcnow()
    await db.commit()

    return make_response(200, data={}, msg="确认受理成功")


@router.post("/{case_id}/appraisal-videos", dependencies=[Depends(require_permission("case:appraisal"))])
async def case_submit_appraisal_videos(
    case_id: Union[str, int],
    body: CaseAppraisalVideosSubmit,
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

    access_err = await _ensure_agency_case_access(row, ctx)
    if access_err:
        return make_response(403, data={}, msg=access_err)

    current_status = int(row.status)
    if current_status not in (STATUS_ACCEPTED, STATUS_REWORK):
        return make_response(500, data={}, msg="当前状态不允许提交鉴定视频")
    if row.agency_id is None:
        return make_response(500, data={}, msg="案件未关联鉴定机构")

    videos = _media_items_to_db(body.appraisalVideos)
    video_err = _validate_stored_videos(videos)
    if video_err:
        return make_response(500, data={}, msg=video_err)

    now = datetime.utcnow()
    row.appraisal_videos = videos
    row.status = STATUS_APPRAISING
    row.updated_at = now
    await db.commit()
    return make_response(200, data={}, msg="鉴定视频提交成功")


@router.post("/{case_id}/document-number", dependencies=[Depends(require_permission("case:appraisal"))])
async def case_submit_document_number(
    case_id: Union[str, int],
    body: CaseDocumentNumberSubmit,
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

    access_err = await _ensure_agency_case_access(row, ctx)
    if access_err:
        return make_response(403, data={}, msg=access_err)

    if int(row.status) != STATUS_APPRAISING:
        return make_response(500, data={}, msg="只有鉴定中状态的案件才能提交文书编号")

    doc_no = body.documentNumber.strip()
    if not doc_no:
        return make_response(500, data={}, msg="鉴定文书编号不能为空")

    now = datetime.utcnow()
    user_id = ctx_user_id.get()
    row.document_number = doc_no
    row.appraisal_submitted_at = now
    row.appraisal_submitted_by = user_id
    row.status = STATUS_COMPLETED
    row.updated_at = now
    await db.commit()
    return make_response(200, data={}, msg="文书编号提交成功，案件已完成")


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

    if ctx.get("agency_id") is not None:
        return make_response(403, data={}, msg="机构账号无权打回案件")

    parsed_id = _parse_case_id(case_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="案件 ID 无效")

    case = await db.get(CaseRecord, parsed_id)
    if not case or case.is_delete == 1:
        return make_response(404, data={}, msg="案件不存在")

    if int(case.status) != STATUS_COMPLETED:
        return make_response(500, data={}, msg="只有已完成状态的案件才能打回重做")

    case.status = STATUS_REWORK
    case.rework_remark = body.remark.strip()
    case.appraisal_videos = None
    case.document_number = None
    case.updated_at = datetime.utcnow()
    await db.commit()

    await _notify_agency_case_event(case, "rework")
    return make_response(200, data={}, msg="打回成功，案件已退回给原鉴定机构重新处理")


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

    now = datetime.utcnow()
    row.is_delete = 1
    row.delete_time = now
    row.report_number = _release_report_number(row.report_number, parsed_id, now)
    row.updated_at = now
    await db.commit()
    return make_response(200, data={}, msg="删除成功")
