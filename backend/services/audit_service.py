from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.agency_user import bind_agency_admin_user
from core.region import normalize_region
from core.dispatch import auto_dispatch_agency, is_case_region_enabled
from models import (
    AppraisalAgency,
    BizAuditRecord,
    BizCaseApplication,
    CaseRecord,
)

BIZ_TYPE_CASE_SUBMIT = "case_submit"
BIZ_TYPE_AGENCY_SUBMIT = "agency_submit"
BIZ_TYPE_AGENCY_ONBOARD = "agency_onboard"

AUDIT_STATUS_PENDING = "pending"
AUDIT_STATUS_APPROVED = "approved"
AUDIT_STATUS_REJECTED = "rejected"

APP_STATUS_PENDING_AUDIT = "pending_audit"
APP_STATUS_REJECTED = "rejected"
APP_STATUS_APPROVED = "approved"

VALID_BIZ_TYPES = (BIZ_TYPE_CASE_SUBMIT, BIZ_TYPE_AGENCY_SUBMIT, BIZ_TYPE_AGENCY_ONBOARD)
VALID_AUDIT_STATUS = (AUDIT_STATUS_PENDING, AUDIT_STATUS_APPROVED, AUDIT_STATUS_REJECTED)

# 案件 status 常量（与 biz_case 路由保持一致）
STATUS_PENDING_CONFIRM = 1
STATUS_APPRAISING = 3
STATUS_COMPLETED = 4
STATUS_REPORT_PENDING_AUDIT = 6

QUERY_PERM_BY_BIZ_TYPE = {
    BIZ_TYPE_CASE_SUBMIT: "case:platformAudit:query",
    BIZ_TYPE_AGENCY_SUBMIT: "case:agencySubmitAudit:query",
    BIZ_TYPE_AGENCY_ONBOARD: "agency:query",
}
APPROVE_PERM_BY_BIZ_TYPE = {
    BIZ_TYPE_CASE_SUBMIT: "case:platformAudit:approve",
    BIZ_TYPE_AGENCY_SUBMIT: "case:agencySubmitAudit:approve",
    BIZ_TYPE_AGENCY_ONBOARD: "agency:audit",
}
REJECT_PERM_BY_BIZ_TYPE = {
    BIZ_TYPE_CASE_SUBMIT: "case:platformAudit:reject",
    BIZ_TYPE_AGENCY_SUBMIT: "case:agencySubmitAudit:reject",
    BIZ_TYPE_AGENCY_ONBOARD: "agency:audit",
}
AGENCY_SUBMIT_AUDIT_PERMS = (
    "case:agencySubmitAudit:query",
    "case:agencySubmitAudit:approve",
    "case:agencySubmitAudit:reject",
)

OVERLAY_VISIBILITY_FULL = "full"
OVERLAY_VISIBILITY_SUMMARY = "summary"
OVERLAY_VISIBILITY_HIDDEN = "hidden"

AUDIT_RECORD_QUERY_PERM = "auditRecord:query"


def _parse_positive_id(raw: Union[str, int, None]) -> Optional[int]:
    try:
        val = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return val if val > 0 else None


def _dt_str(dt: Optional[datetime]) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


def _date_str(d: Optional[date]) -> str:
    return d.strftime("%Y-%m-%d") if d else ""


def query_perm_for_biz_type(biz_type: str) -> str:
    return QUERY_PERM_BY_BIZ_TYPE[biz_type]


def approve_perm_for_biz_type(biz_type: str) -> str:
    return APPROVE_PERM_BY_BIZ_TYPE[biz_type]


def reject_perm_for_biz_type(biz_type: str) -> str:
    return REJECT_PERM_BY_BIZ_TYPE[biz_type]


def collect_perm_codes(bundle: Dict[str, Any]) -> set[str]:
    return set(bundle.get("codes") or [])


def resolve_list_biz_type_filter(
    perm_codes: set[str],
    biz_type: Optional[str],
) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    解析列表查询的业务类型过滤。
    返回 (error_msg, allowed_biz_types)。
    allowed_biz_types=None 表示不过滤（审核记录页看全量）；
    allowed_biz_types=[...] 表示仅返回用户有 query 权限的子类型。
    """
    if biz_type:
        if biz_type not in VALID_BIZ_TYPES:
            return "bizType 参数无效", None
        if query_perm_for_biz_type(biz_type) not in perm_codes:
            return "无权限访问", None
        return None, [biz_type]

    if AUDIT_RECORD_QUERY_PERM in perm_codes:
        return None, None

    allowed = [bt for bt in VALID_BIZ_TYPES if query_perm_for_biz_type(bt) in perm_codes]
    if not allowed:
        return "无权限访问", None
    return None, allowed


def can_view_audit_detail(perm_codes: set[str], biz_type: str) -> bool:
    if query_perm_for_biz_type(biz_type) in perm_codes:
        return True
    return AUDIT_RECORD_QUERY_PERM in perm_codes


async def _lock_biz_entity_for_audit(
    db: AsyncSession,
    biz_type: str,
    biz_id: int,
) -> Optional[str]:
    if biz_type == BIZ_TYPE_CASE_SUBMIT:
        stmt = select(BizCaseApplication).where(BizCaseApplication.id == biz_id).with_for_update()
        if (await db.scalars(stmt)).first() is None:
            return "申请单不存在"
        return None
    if biz_type == BIZ_TYPE_AGENCY_SUBMIT:
        stmt = select(CaseRecord).where(CaseRecord.id == biz_id, CaseRecord.is_delete == 0).with_for_update()
        if (await db.scalars(stmt)).first() is None:
            return "案件不存在"
        return None
    if biz_type == BIZ_TYPE_AGENCY_ONBOARD:
        stmt = select(AppraisalAgency).where(AppraisalAgency.id == biz_id, AppraisalAgency.is_delete == 0).with_for_update()
        if (await db.scalars(stmt)).first() is None:
            return "机构不存在"
        return None
    return "biz_type 无效"


async def _lock_audit_records_for_biz(db: AsyncSession, biz_type: str, biz_id: int) -> None:
    stmt = (
        select(BizAuditRecord)
        .where(BizAuditRecord.biz_type == biz_type, BizAuditRecord.biz_id == biz_id)
        .with_for_update()
    )
    await db.scalars(stmt)


async def _get_next_submit_batch_locked(db: AsyncSession, biz_type: str, biz_id: int) -> int:
    stmt = select(func.max(BizAuditRecord.submit_batch)).where(
        BizAuditRecord.biz_type == biz_type,
        BizAuditRecord.biz_id == biz_id,
    )
    current = await db.scalar(stmt)
    return int(current or 0) + 1


async def get_pending_audit(
    db: AsyncSession,
    biz_type: str,
    biz_id: int,
) -> Optional[BizAuditRecord]:
    stmt = (
        select(BizAuditRecord)
        .where(
            BizAuditRecord.biz_type == biz_type,
            BizAuditRecord.biz_id == biz_id,
            BizAuditRecord.status == AUDIT_STATUS_PENDING,
        )
        .limit(1)
    )
    return (await db.scalars(stmt)).first()


async def _get_pending_audit_locked(
    db: AsyncSession,
    biz_type: str,
    biz_id: int,
) -> Optional[BizAuditRecord]:
    stmt = (
        select(BizAuditRecord)
        .where(
            BizAuditRecord.biz_type == biz_type,
            BizAuditRecord.biz_id == biz_id,
            BizAuditRecord.status == AUDIT_STATUS_PENDING,
        )
        .with_for_update()
        .limit(1)
    )
    return (await db.scalars(stmt)).first()


CASE_MATERIAL_CATEGORY_POLICY = "policy"
CASE_MATERIAL_CATEGORY_ACCIDENT_DECISION = "accident_decision"
VALID_CASE_MATERIAL_CATEGORIES = (
    CASE_MATERIAL_CATEGORY_POLICY,
    CASE_MATERIAL_CATEGORY_ACCIDENT_DECISION,
)
MAX_CASE_MATERIAL_COUNT = 9


def _validate_attachment_items(items: List[Any]) -> Optional[str]:
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            return f"attachments[{idx}] 须为对象"
        url = str(item.get("url") or "").strip()
        if not url:
            return f"attachments[{idx}] 缺少 url"
    return None


def _attachment_dedupe_key(item: Dict[str, Any]) -> str:
    url = str(item.get("url") or "").strip()
    name = str(item.get("name") or "").strip()
    return f"{url}|{name}"


def _is_image_material(item: Dict[str, Any]) -> bool:
    kind = str(item.get("kind") or "").strip().lower()
    if kind == "image":
        return True
    if kind in ("pdf", "file"):
        return False
    probe = f"{item.get('name') or ''} {item.get('url') or ''}".lower()
    if re.search(r"\.pdf($|\?)", probe):
        return False
    return bool(re.search(r"\.(png|jpe?g|gif|webp|bmp)($|\?)", probe))


def _coerce_material_item(
    raw: Any,
    *,
    default_category: str,
) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    url = str(raw.get("url") or "").strip()
    if not url:
        return None
    category = str(raw.get("category") or default_category).strip()
    if category not in VALID_CASE_MATERIAL_CATEGORIES:
        return None
    name = str(raw.get("name") or "").strip()
    item: Dict[str, Any] = {
        "url": url,
        "kind": "image",
        "category": category,
    }
    if name:
        item["name"] = name
    return item


def normalize_case_materials(
    *,
    policy_images: Optional[List[Any]] = None,
    accident_decision_images: Optional[List[Any]] = None,
    attachments: Optional[List[Any]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """合并结构化字段与 attachments，输出带 category 的统一材料快照。"""
    policy_out: List[Dict[str, Any]] = []
    accident_out: List[Dict[str, Any]] = []
    merged: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def append_item(raw: Any, default_category: str) -> None:
        item = _coerce_material_item(raw, default_category=default_category)
        if item is None:
            return
        key = _attachment_dedupe_key(item)
        if key in seen:
            return
        seen.add(key)
        category = item["category"]
        if category == CASE_MATERIAL_CATEGORY_POLICY:
            policy_out.append(dict(item))
        else:
            accident_out.append(dict(item))
        merged.append(dict(item))

    for raw in policy_images or []:
        append_item(raw, CASE_MATERIAL_CATEGORY_POLICY)
    for raw in accident_decision_images or []:
        append_item(raw, CASE_MATERIAL_CATEGORY_ACCIDENT_DECISION)
    for raw in attachments or []:
        if not isinstance(raw, dict):
            continue
        category = str(raw.get("category") or "").strip()
        if category not in VALID_CASE_MATERIAL_CATEGORIES:
            continue
        append_item(raw, category)

    return {
        "policyImages": policy_out,
        "accidentDecisionImages": accident_out,
        "attachments": merged,
    }


def validate_case_materials(
    materials: Dict[str, List[Dict[str, Any]]],
    *,
    require_policy: bool = True,
) -> Optional[str]:
    for key in ("policyImages", "accidentDecisionImages"):
        items = materials.get(key) or []
        if len(items) > MAX_CASE_MATERIAL_COUNT:
            label = "保单图片" if key == "policyImages" else "事故认定书图片"
            return f"{label}最多 {MAX_CASE_MATERIAL_COUNT} 张"

    for idx, item in enumerate(materials.get("attachments") or []):
        if not isinstance(item, dict):
            return f"材料[{idx}] 格式无效"
        if not _is_image_material(item):
            return f"材料[{idx}] 仅支持图片"
        category = str(item.get("category") or "").strip()
        if category not in VALID_CASE_MATERIAL_CATEGORIES:
            return f"材料[{idx}] category 无效"

    if require_policy and len(materials.get("policyImages") or []) < 1:
        return "请至少上传 1 张保单图片"
    return None


def materials_from_request_body(body: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    return normalize_case_materials(
        policy_images=body.get("policyImages"),
        accident_decision_images=body.get("accidentDecisionImages"),
        attachments=body.get("attachments"),
    )


def _validate_resubmit_body(body: Dict[str, Any], app: BizCaseApplication) -> Optional[str]:
    region_keys = ("province", "city", "district")
    region_present = [k for k in region_keys if body.get(k) is not None]
    if region_present and len(region_present) != 3:
        return "省/市/区县须同时提交"

    if body.get("victimName") is not None and not str(body["victimName"]).strip():
        return "伤者姓名不能为空"
    if body.get("victimPhone") is not None and not str(body["victimPhone"]).strip():
        return "联系电话不能为空"
    if body.get("accidentType") is not None and not str(body["accidentType"]).strip():
        return "事故类型不能为空"
    if body.get("injuryType") is not None and not str(body["injuryType"]).strip():
        return "伤情类型不能为空"

    for key in ("reportNumber", "reportDate", "insuranceCompany"):
        if body.get(key) is not None:
            return f"驳回后补件不可修改 {key}"

    materials = materials_from_request_body(body)
    mat_err = validate_case_materials(materials, require_policy=False)
    if mat_err:
        return mat_err

    if body.get("province") is not None:
        p, c, d = normalize_region(
            str(body["province"]).strip(),
            str(body["city"]).strip(),
            str(body["district"]).strip(),
        )
        if not p or not c or not d:
            return "省/市/区县不能为空"

    _ = app
    return None


async def create_audit_record(
    db: AsyncSession,
    *,
    biz_type: str,
    biz_id: int,
    submit_payload: Optional[Dict[str, Any]],
    created_by: Optional[int],
    idempotency_key: Optional[str] = None,
) -> BizAuditRecord:
    if biz_id <= 0:
        raise ValueError("biz_id 必须大于 0")
    if biz_type not in VALID_BIZ_TYPES:
        raise ValueError("biz_type 无效")

    lock_err = await _lock_biz_entity_for_audit(db, biz_type, biz_id)
    if lock_err:
        raise ValueError(lock_err)
    await _lock_audit_records_for_biz(db, biz_type, biz_id)

    if await _get_pending_audit_locked(db, biz_type, biz_id) is not None:
        raise ValueError("存在待审核记录，请勿重复提交")

    batch = await _get_next_submit_batch_locked(db, biz_type, biz_id)
    now = datetime.utcnow()
    row = BizAuditRecord(
        biz_type=biz_type,
        biz_id=biz_id,
        submit_batch=batch,
        status=AUDIT_STATUS_PENDING,
        submit_payload=submit_payload,
        created_by=created_by,
        idempotency_key=idempotency_key,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    await db.flush()
    return row


def _application_summary(app: BizCaseApplication) -> Dict[str, Any]:
    return {
        "reportNumber": app.report_number,
        "victimName": app.victim_name,
        "victimPhone": app.victim_phone,
        "reportDate": _date_str(app.report_date),
        "province": app.province,
        "city": app.city,
        "district": app.district,
        "accidentType": app.accident_type,
        "injuryType": app.injury_type,
        "insuranceCompany": app.insurance_company,
        "appStatus": app.app_status,
        "caseId": str(app.case_id) if app.case_id else None,
    }


def _case_summary(case: CaseRecord) -> Dict[str, Any]:
    return {
        "reportNumber": case.report_number,
        "victimName": case.victim_name,
        "status": int(case.status),
        "agencyId": case.agency_id,
    }


def _agency_summary(agency: AppraisalAgency) -> Dict[str, Any]:
    return {
        "agencyName": agency.agency_name,
        "contactPerson": agency.contact_person,
        "contactPhone": agency.contact_phone,
        "province": agency.province,
        "city": agency.city,
        "district": agency.district,
        "address": agency.address,
        "agencyStatus": int(agency.status),
    }


async def _load_biz_summary(
    db: AsyncSession,
    biz_type: str,
    biz_id: int,
) -> Optional[Dict[str, Any]]:
    if biz_type == BIZ_TYPE_CASE_SUBMIT:
        app = await db.get(BizCaseApplication, biz_id)
        return _application_summary(app) if app else None
    if biz_type == BIZ_TYPE_AGENCY_SUBMIT:
        case = await db.get(CaseRecord, biz_id)
        if case is None or case.is_delete == 1:
            return None
        return _case_summary(case)
    if biz_type == BIZ_TYPE_AGENCY_ONBOARD:
        agency = await db.get(AppraisalAgency, biz_id)
        if agency is None or agency.is_delete == 1:
            return None
        return _agency_summary(agency)
    return None


def audit_record_row(row: BizAuditRecord, summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "bizType": row.biz_type,
        "bizId": str(row.biz_id),
        "submitBatch": int(row.submit_batch),
        "status": row.status,
        "submitPayload": row.submit_payload,
        "auditRemark": row.audit_remark or "",
        "auditedBy": row.audited_by,
        "auditedAt": _dt_str(row.audited_at),
        "createdBy": row.created_by,
        "createdAt": _dt_str(row.created_at),
        "updatedAt": _dt_str(row.updated_at),
        "summary": summary,
    }


def batch_history_item(row: BizAuditRecord) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "submitBatch": int(row.submit_batch),
        "status": row.status,
        "submitPayload": row.submit_payload,
        "auditRemark": row.audit_remark or "",
        "auditedBy": row.audited_by,
        "auditedAt": _dt_str(row.audited_at),
        "createdAt": _dt_str(row.created_at),
    }


async def list_audit_records(
    db: AsyncSession,
    *,
    page_num: int,
    page_size: int,
    biz_type: Optional[str],
    status: Optional[str],
    allowed_biz_types: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    stmt = select(BizAuditRecord)
    if biz_type:
        if biz_type not in VALID_BIZ_TYPES:
            raise ValueError("bizType 参数无效")
        stmt = stmt.where(BizAuditRecord.biz_type == biz_type)
    elif allowed_biz_types is not None:
        stmt = stmt.where(BizAuditRecord.biz_type.in_(allowed_biz_types))
    if status:
        if status not in VALID_AUDIT_STATUS:
            raise ValueError("status 参数无效")
        stmt = stmt.where(BizAuditRecord.status == status)

    count_stmt = select(func.count()).select_from(BizAuditRecord).where(*stmt._where_criteria)
    total = int((await db.scalar(count_stmt)) or 0)

    stmt = stmt.order_by(BizAuditRecord.created_at.desc(), BizAuditRecord.id.desc())
    stmt = stmt.offset((page_num - 1) * page_size).limit(page_size)
    rows = list((await db.scalars(stmt)).all())

    out: List[Dict[str, Any]] = []
    for row in rows:
        summary = await _load_biz_summary(db, row.biz_type, row.biz_id)
        out.append(audit_record_row(row, summary))
    return out, total


async def get_audit_detail(db: AsyncSession, audit_id: int) -> Optional[Dict[str, Any]]:
    row = await db.get(BizAuditRecord, audit_id)
    if row is None:
        return None

    history_stmt = (
        select(BizAuditRecord)
        .where(
            BizAuditRecord.biz_type == row.biz_type,
            BizAuditRecord.biz_id == row.biz_id,
        )
        .order_by(BizAuditRecord.submit_batch.asc(), BizAuditRecord.id.asc())
    )
    history_rows = list((await db.scalars(history_stmt)).all())
    summary = await _load_biz_summary(db, row.biz_type, row.biz_id)

    data = audit_record_row(row, summary)
    data["batchHistory"] = [batch_history_item(h) for h in history_rows]
    return data


async def _ensure_report_number_available(
    db: AsyncSession,
    report_number: str,
    exclude_case_id: Optional[int] = None,
) -> Optional[str]:
    stmt = select(CaseRecord.id).where(
        CaseRecord.report_number == report_number,
        CaseRecord.is_delete == 0,
    )
    if exclude_case_id is not None:
        stmt = stmt.where(CaseRecord.id != exclude_case_id)
    if (await db.scalars(stmt.limit(1))).first() is not None:
        return "出险报案号已存在"
    return None


async def _approve_case_submit(
    db: AsyncSession,
    audit: BizAuditRecord,
    auditor_id: Optional[int],
) -> Optional[str]:
    app = await db.get(BizCaseApplication, audit.biz_id)
    if app is None:
        return "申请单不存在"

    dup_msg = await _ensure_report_number_available(db, app.report_number)
    if dup_msg:
        return dup_msg

    agency_id = await auto_dispatch_agency(db, app.province, app.city, app.district)
    now = datetime.utcnow()

    case = CaseRecord(
        report_number=app.report_number,
        victim_name=app.victim_name,
        victim_phone=app.victim_phone,
        report_date=app.report_date,
        province=app.province,
        city=app.city,
        district=app.district,
        accident_type=app.accident_type,
        injury_type=app.injury_type,
        insurance_company=app.insurance_company,
        status=STATUS_PENDING_CONFIRM,
        agency_id=agency_id,
        dept_id=None,
        created_by=app.created_by,
        created_at=now,
        updated_at=now,
    )
    db.add(case)
    await db.flush()

    app.case_id = case.id
    app.app_status = APP_STATUS_APPROVED
    app.is_active = 0
    app.closed_at = now
    app.updated_at = now

    audit.status = AUDIT_STATUS_APPROVED
    audit.audited_by = auditor_id
    audit.audited_at = now
    audit.updated_at = now
    return None


async def _approve_agency_submit(
    db: AsyncSession,
    audit: BizAuditRecord,
    auditor_id: Optional[int],
) -> Optional[str]:
    case = await db.get(CaseRecord, audit.biz_id)
    if case is None or case.is_delete == 1:
        return "案件不存在"

    if int(case.status) != STATUS_REPORT_PENDING_AUDIT:
        return "案件状态不是报告待平台审核"

    payload = audit.submit_payload or {}
    doc_no = str(payload.get("documentNumber") or "").strip()
    certificate = payload.get("electronicCertificate")
    if not doc_no:
        return "审核快照缺少鉴定文书编号"
    if not certificate or not isinstance(certificate, dict):
        return "审核快照缺少电子证书"

    now = datetime.utcnow()
    case.document_number = doc_no
    case.electronic_certificate = certificate
    case.appraisal_submitted_at = now
    case.appraisal_submitted_by = audit.created_by
    case.status = STATUS_COMPLETED
    case.updated_at = now

    audit.status = AUDIT_STATUS_APPROVED
    audit.audited_by = auditor_id
    audit.audited_at = now
    audit.updated_at = now
    return None


async def _approve_agency_onboard(
    db: AsyncSession,
    audit: BizAuditRecord,
    auditor_id: Optional[int],
) -> Tuple[Optional[str], str]:
    agency = await db.get(AppraisalAgency, audit.biz_id)
    if agency is None or agency.is_delete == 1:
        return "机构不存在", ""

    now = datetime.utcnow()
    agency.status = 1
    agency.audit_remark = None
    agency.updated_at = now

    audit.status = AUDIT_STATUS_APPROVED
    audit.audited_by = auditor_id
    audit.audited_at = now
    audit.updated_at = now

    suffix, _ = await bind_agency_admin_user(db, agency)
    return None, suffix


async def approve_audit(
    db: AsyncSession,
    audit_id: int,
    auditor_id: Optional[int],
) -> Tuple[Optional[str], str]:
    stmt = select(BizAuditRecord).where(BizAuditRecord.id == audit_id).with_for_update()
    audit = (await db.scalars(stmt)).first()
    if audit is None:
        return "审核记录不存在", ""
    if audit.status != AUDIT_STATUS_PENDING:
        return "该记录已审核，无法重复操作", ""

    lock_err = await _lock_biz_entity_for_audit(db, audit.biz_type, audit.biz_id)
    if lock_err:
        return lock_err, ""

    msg = ""
    if audit.biz_type == BIZ_TYPE_CASE_SUBMIT:
        err = await _approve_case_submit(db, audit, auditor_id)
        if err:
            return err, ""
    elif audit.biz_type == BIZ_TYPE_AGENCY_SUBMIT:
        err = await _approve_agency_submit(db, audit, auditor_id)
        if err:
            return err, ""
    elif audit.biz_type == BIZ_TYPE_AGENCY_ONBOARD:
        err, suffix = await _approve_agency_onboard(db, audit, auditor_id)
        if err:
            return err, ""
        msg = suffix
    else:
        return "未知业务类型", ""

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return "审核通过失败：数据冲突", ""
    return None, msg


async def _reject_case_submit(
    db: AsyncSession,
    audit: BizAuditRecord,
    remark: str,
    auditor_id: Optional[int],
) -> Optional[str]:
    app = await db.get(BizCaseApplication, audit.biz_id)
    if app is None:
        return "申请单不存在"

    now = datetime.utcnow()
    app.app_status = APP_STATUS_REJECTED
    app.updated_at = now

    audit.status = AUDIT_STATUS_REJECTED
    audit.audit_remark = remark
    audit.audited_by = auditor_id
    audit.audited_at = now
    audit.updated_at = now
    return None


async def _reject_agency_submit(
    db: AsyncSession,
    audit: BizAuditRecord,
    remark: str,
    auditor_id: Optional[int],
) -> Optional[str]:
    case = await db.get(CaseRecord, audit.biz_id)
    if case is None or case.is_delete == 1:
        return "案件不存在"
    if int(case.status) != STATUS_REPORT_PENDING_AUDIT:
        return "案件状态不是报告待平台审核"

    now = datetime.utcnow()
    case.status = STATUS_APPRAISING
    case.updated_at = now

    audit.status = AUDIT_STATUS_REJECTED
    audit.audit_remark = remark
    audit.audited_by = auditor_id
    audit.audited_at = now
    audit.updated_at = now
    return None


async def _reject_agency_onboard(
    db: AsyncSession,
    audit: BizAuditRecord,
    remark: str,
    auditor_id: Optional[int],
) -> Optional[str]:
    agency = await db.get(AppraisalAgency, audit.biz_id)
    if agency is None or agency.is_delete == 1:
        return "机构不存在"

    now = datetime.utcnow()
    agency.status = 3
    agency.audit_remark = remark
    agency.updated_at = now

    audit.status = AUDIT_STATUS_REJECTED
    audit.audit_remark = remark
    audit.audited_by = auditor_id
    audit.audited_at = now
    audit.updated_at = now
    return None


async def reject_audit(
    db: AsyncSession,
    audit_id: int,
    remark: str,
    auditor_id: Optional[int],
) -> Optional[str]:
    stmt = select(BizAuditRecord).where(BizAuditRecord.id == audit_id).with_for_update()
    audit = (await db.scalars(stmt)).first()
    if audit is None:
        return "审核记录不存在"
    if audit.status != AUDIT_STATUS_PENDING:
        return "该记录已审核，无法重复操作"

    lock_err = await _lock_biz_entity_for_audit(db, audit.biz_type, audit.biz_id)
    if lock_err:
        return lock_err

    if audit.biz_type == BIZ_TYPE_CASE_SUBMIT:
        err = await _reject_case_submit(db, audit, remark, auditor_id)
    elif audit.biz_type == BIZ_TYPE_AGENCY_SUBMIT:
        err = await _reject_agency_submit(db, audit, remark, auditor_id)
    elif audit.biz_type == BIZ_TYPE_AGENCY_ONBOARD:
        err = await _reject_agency_onboard(db, audit, remark, auditor_id)
    else:
        return "未知业务类型"

    if err:
        return err

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return "审核驳回失败：数据冲突"
    return None


async def resubmit_case_submit(
    db: AsyncSession,
    application_id: int,
    body: Dict[str, Any],
    user_id: Optional[int],
) -> Optional[str]:
    lock_err = await _lock_biz_entity_for_audit(db, BIZ_TYPE_CASE_SUBMIT, application_id)
    if lock_err:
        return lock_err

    stmt = select(BizCaseApplication).where(BizCaseApplication.id == application_id).with_for_update()
    app = (await db.scalars(stmt)).first()
    if app is None:
        return "申请单不存在"
    if app.app_status != APP_STATUS_REJECTED:
        return "只有已驳回的申请才能补件提交"
    if user_id is not None and app.created_by != user_id:
        return "无权操作该申请单"

    validate_err = _validate_resubmit_body(body, app)
    if validate_err:
        return validate_err

    await _lock_audit_records_for_biz(db, BIZ_TYPE_CASE_SUBMIT, application_id)
    if await _get_pending_audit_locked(db, BIZ_TYPE_CASE_SUBMIT, application_id) is not None:
        return "存在待审核记录，请勿重复提交"

    if body.get("victimName") is not None:
        app.victim_name = str(body["victimName"]).strip()
    if body.get("victimPhone") is not None:
        app.victim_phone = str(body["victimPhone"]).strip()
    if body.get("province") is not None and body.get("city") is not None and body.get("district") is not None:
        p, c, d = normalize_region(
            str(body["province"]).strip(),
            str(body["city"]).strip(),
            str(body["district"]).strip(),
        )
        if not await is_case_region_enabled(db, p, c, d):
            return "该地区暂未开放业务，请联系平台管理员"
        app.province, app.city, app.district = p, c, d
    if body.get("accidentType") is not None:
        app.accident_type = str(body["accidentType"]).strip()
    if body.get("injuryType") is not None:
        app.injury_type = str(body["injuryType"]).strip()

    materials = materials_from_request_body(body)

    payload: Dict[str, Any] = {
        "applicationId": application_id,
        "reportNumber": app.report_number,
        "victimName": app.victim_name,
        "victimPhone": app.victim_phone,
        "reportDate": _date_str(app.report_date),
        "province": app.province,
        "city": app.city,
        "district": app.district,
        "accidentType": app.accident_type,
        "injuryType": app.injury_type,
        "insuranceCompany": app.insurance_company,
        "policyImages": materials["policyImages"],
        "accidentDecisionImages": materials["accidentDecisionImages"],
        "attachments": materials["attachments"],
    }

    now = datetime.utcnow()
    app.app_status = APP_STATUS_PENDING_AUDIT
    app.updated_at = now

    batch = await _get_next_submit_batch_locked(db, BIZ_TYPE_CASE_SUBMIT, application_id)
    db.add(
        BizAuditRecord(
            biz_type=BIZ_TYPE_CASE_SUBMIT,
            biz_id=application_id,
            submit_batch=batch,
            status=AUDIT_STATUS_PENDING,
            submit_payload=payload,
            created_by=user_id,
            created_at=now,
            updated_at=now,
        )
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return "补件提交失败：存在并发冲突或重复待审记录"
    return None


def build_case_submit_payload(
    app: BizCaseApplication,
    *,
    materials: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    attachments: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    normalized = materials or normalize_case_materials(attachments=attachments or [])
    return {
        "applicationId": app.id,
        "reportNumber": app.report_number,
        "victimName": app.victim_name,
        "victimPhone": app.victim_phone,
        "reportDate": _date_str(app.report_date),
        "province": app.province,
        "city": app.city,
        "district": app.district,
        "accidentType": app.accident_type,
        "injuryType": app.injury_type,
        "insuranceCompany": app.insurance_company,
        "policyImages": normalized["policyImages"],
        "accidentDecisionImages": normalized["accidentDecisionImages"],
        "attachments": normalized["attachments"],
    }


def build_agency_onboard_payload(agency: AppraisalAgency) -> Dict[str, Any]:
    return {
        "agencyId": agency.id,
        "agencyName": agency.agency_name,
        "contactPerson": agency.contact_person,
        "contactPhone": agency.contact_phone,
        "province": agency.province,
        "city": agency.city,
        "district": agency.district,
        "address": agency.address,
    }


async def ensure_report_number_for_new_application(
    db: AsyncSession,
    report_number: str,
) -> Optional[str]:
    """§2.1.1：案件表 + 活跃申请单占用校验（含 FOR UPDATE）。"""
    case_err = await _ensure_report_number_available(db, report_number)
    if case_err:
        return case_err

    stmt = (
        select(BizCaseApplication.id)
        .where(
            BizCaseApplication.report_number == report_number,
            BizCaseApplication.is_active == 1,
            BizCaseApplication.case_id.is_(None),
        )
        .with_for_update()
        .limit(1)
    )
    if (await db.scalars(stmt)).first() is not None:
        return "该报案号已有进行中的申请"
    return None


async def has_any_audit_record(db: AsyncSession, biz_type: str, biz_id: int) -> bool:
    stmt = (
        select(BizAuditRecord.id)
        .where(BizAuditRecord.biz_type == biz_type, BizAuditRecord.biz_id == biz_id)
        .limit(1)
    )
    return (await db.scalars(stmt)).first() is not None


async def create_case_submit_application(
    db: AsyncSession,
    *,
    report_number: str,
    victim_name: str,
    victim_phone: str,
    report_date: date,
    province: str,
    city: str,
    district: str,
    accident_type: str,
    injury_type: str,
    insurance_company: str,
    created_by: Optional[int],
    materials: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    attachments: Optional[List[Any]] = None,
) -> Tuple[Optional[str], Optional[int]]:
    dup_msg = await ensure_report_number_for_new_application(db, report_number)
    if dup_msg:
        return dup_msg, None

    now = datetime.utcnow()
    app = BizCaseApplication(
        report_number=report_number,
        victim_name=victim_name,
        victim_phone=victim_phone,
        report_date=report_date,
        province=province,
        city=city,
        district=district,
        accident_type=accident_type,
        injury_type=injury_type,
        insurance_company=insurance_company,
        created_by=created_by,
        app_status=APP_STATUS_PENDING_AUDIT,
        is_active=1,
        created_at=now,
        updated_at=now,
    )
    db.add(app)
    await db.flush()

    normalized = materials or normalize_case_materials(attachments=attachments or [])
    mat_err = validate_case_materials(normalized, require_policy=True)
    if mat_err:
        await db.rollback()
        return mat_err, None

    try:
        await create_audit_record(
            db,
            biz_type=BIZ_TYPE_CASE_SUBMIT,
            biz_id=app.id,
            submit_payload=build_case_submit_payload(app, materials=normalized),
            created_by=created_by,
        )
        await db.commit()
    except (ValueError, IntegrityError) as exc:
        await db.rollback()
        if isinstance(exc, ValueError):
            return str(exc), None
        return "报案提交失败：存在并发冲突或重复待审记录", None
    return None, app.id


def _resolve_document_overlay_for_case(
    case: CaseRecord,
    audits: List[BizAuditRecord],
) -> Dict[str, Any]:
    st = int(case.status)
    pending = next((a for a in audits if a.status == AUDIT_STATUS_PENDING), None)
    rejected = [a for a in audits if a.status == AUDIT_STATUS_REJECTED]
    has_any = bool(audits)

    if st == STATUS_REPORT_PENDING_AUDIT:
        payload = (pending.submit_payload or {}) if pending else {}
        return {
            "documentFieldsSource": "pending_payload" if pending else "hidden",
            "documentNumber": str(payload.get("documentNumber") or "").strip() or None,
            "electronicCertificate": payload.get("electronicCertificate"),
            "pendingAgencySubmitAuditId": str(pending.id) if pending else None,
        }

    if st == STATUS_APPRAISING and rejected and not pending:
        latest = max(rejected, key=lambda a: int(a.submit_batch))
        return {
            "documentFieldsSource": "hidden",
            "documentNumber": None,
            "electronicCertificate": None,
            "latestAgencySubmitRejectRemark": latest.audit_remark or "",
        }

    if st == STATUS_APPRAISING and not has_any and (case.document_number or case.electronic_certificate):
        return {"documentFieldsSource": "legacy_main"}

    return {"documentFieldsSource": "main"}


async def load_agency_submit_batch_histories(
    db: AsyncSession,
    case_ids: List[int],
) -> Dict[int, List[Dict[str, Any]]]:
    if not case_ids:
        return {}
    stmt = (
        select(BizAuditRecord)
        .where(
            BizAuditRecord.biz_type == BIZ_TYPE_AGENCY_SUBMIT,
            BizAuditRecord.biz_id.in_(case_ids),
        )
        .order_by(BizAuditRecord.biz_id.asc(), BizAuditRecord.submit_batch.asc())
    )
    rows = list((await db.scalars(stmt)).all())
    grouped: Dict[int, List[BizAuditRecord]] = {cid: [] for cid in case_ids}
    for row in rows:
        grouped.setdefault(int(row.biz_id), []).append(row)
    return {cid: build_agency_submit_batch_history(grouped.get(cid, [])) for cid in case_ids}


async def load_agency_submit_overlays(
    db: AsyncSession,
    cases: List[CaseRecord],
) -> Dict[int, Dict[str, Any]]:
    if not cases:
        return {}

    case_ids = [int(c.id) for c in cases]
    stmt = (
        select(BizAuditRecord)
        .where(
            BizAuditRecord.biz_type == BIZ_TYPE_AGENCY_SUBMIT,
            BizAuditRecord.biz_id.in_(case_ids),
        )
        .order_by(BizAuditRecord.biz_id.asc(), BizAuditRecord.submit_batch.asc())
    )
    rows = list((await db.scalars(stmt)).all())
    audits_by_case: Dict[int, List[BizAuditRecord]] = {cid: [] for cid in case_ids}
    for row in rows:
        audits_by_case.setdefault(int(row.biz_id), []).append(row)

    return {
        int(case.id): _resolve_document_overlay_for_case(case, audits_by_case.get(int(case.id), []))
        for case in cases
    }


async def resolve_agency_submit_overlay_visibility(
    db: AsyncSession,
    ctx: dict,
    *,
    for_detail: bool,
) -> str:
    """
    控制 pending 文书 overlay 可见级别：
    - full：详情可见文书号 + 证书 + pendingAgencySubmitAuditId
    - summary：列表可见文书号摘要 + pendingAgencySubmitAuditId（不含证书）
    - hidden：仅保留 status=6 等状态，不暴露待审文书包
    """
    if ctx.get("is_superuser"):
        return OVERLAY_VISIBILITY_FULL if for_detail else OVERLAY_VISIBILITY_SUMMARY
    roles = ctx.get("roles") or []
    if "admin" in roles:
        return OVERLAY_VISIBILITY_FULL if for_detail else OVERLAY_VISIBILITY_SUMMARY
    if ctx.get("agency_id") is not None:
        return OVERLAY_VISIBILITY_FULL if for_detail else OVERLAY_VISIBILITY_SUMMARY

    from api.deps import get_user_perms_bundle

    bundle = await db.run_sync(lambda s: get_user_perms_bundle(s, ctx))
    codes = collect_perm_codes(bundle)
    if any(code in codes for code in AGENCY_SUBMIT_AUDIT_PERMS):
        return OVERLAY_VISIBILITY_FULL if for_detail else OVERLAY_VISIBILITY_SUMMARY
    return OVERLAY_VISIBILITY_HIDDEN


def sanitize_agency_submit_overlay(
    overlay: Optional[Dict[str, Any]],
    visibility: str,
) -> Optional[Dict[str, Any]]:
    if not overlay:
        return overlay

    source = overlay.get("documentFieldsSource")
    has_reject_remark = bool(overlay.get("latestAgencySubmitRejectRemark"))
    if source != "pending_payload" and not has_reject_remark:
        return overlay

    if visibility == OVERLAY_VISIBILITY_FULL:
        return overlay

    if visibility == OVERLAY_VISIBILITY_SUMMARY:
        sanitized = dict(overlay)
        sanitized["electronicCertificate"] = None
        return sanitized

    sanitized = dict(overlay)
    if source == "pending_payload":
        sanitized["documentFieldsSource"] = "hidden"
        sanitized["documentNumber"] = None
        sanitized["electronicCertificate"] = None
        sanitized["pendingAgencySubmitAuditId"] = None
    if has_reject_remark:
        sanitized.pop("latestAgencySubmitRejectRemark", None)
    return sanitized


def sanitize_agency_submit_overlay_map(
    overlays: Dict[int, Dict[str, Any]],
    visibility: str,
) -> Dict[int, Dict[str, Any]]:
    return {
        case_id: sanitize_agency_submit_overlay(overlay, visibility)
        for case_id, overlay in overlays.items()
    }


def _merge_attachments_from_audits(audits: List[BizAuditRecord]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for audit in sorted(audits, key=lambda a: int(a.submit_batch)):
        payload = audit.submit_payload or {}
        batch_attachments = payload.get("attachments") or []
        if isinstance(batch_attachments, list):
            for item in batch_attachments:
                if isinstance(item, dict):
                    key = _attachment_dedupe_key(item)
                    if key in seen:
                        continue
                    seen.add(key)
                    merged.append(item)
    return merged


def _merge_categorized_materials_from_audits(
    audits: List[BizAuditRecord],
    *,
    structured_field: str,
    category: str,
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def append_item(item: Dict[str, Any]) -> None:
        key = _attachment_dedupe_key(item)
        if key in seen:
            return
        seen.add(key)
        merged.append(item)

    for audit in sorted(audits, key=lambda a: int(a.submit_batch)):
        payload = audit.submit_payload or {}
        structured = payload.get(structured_field) or []
        if isinstance(structured, list):
            for raw in structured:
                coerced = _coerce_material_item(raw, default_category=category)
                if coerced is not None:
                    append_item(coerced)
        batch_attachments = payload.get("attachments") or []
        if isinstance(batch_attachments, list):
            for raw in batch_attachments:
                if not isinstance(raw, dict):
                    continue
                if str(raw.get("category") or "").strip() != category:
                    continue
                coerced = _coerce_material_item(raw, default_category=category)
                if coerced is not None:
                    append_item(coerced)
    return merged


def build_agency_submit_batch_history(audits: List[BizAuditRecord]) -> List[Dict[str, Any]]:
    return [batch_history_item(a) for a in sorted(audits, key=lambda a: int(a.submit_batch))]


def _latest_reject_remark(audits: List[BizAuditRecord]) -> str:
    rejected = [a for a in audits if a.status == AUDIT_STATUS_REJECTED]
    if not rejected:
        return ""
    latest = max(rejected, key=lambda a: int(a.submit_batch))
    return latest.audit_remark or ""


def application_list_row(
    app: BizCaseApplication,
    *,
    audits: List[BizAuditRecord],
) -> Dict[str, Any]:
    pending = next((a for a in audits if a.status == AUDIT_STATUS_PENDING), None)
    return {
        "id": str(app.id),
        "reportNumber": app.report_number,
        "victimName": app.victim_name,
        "victimPhone": app.victim_phone,
        "reportDate": _date_str(app.report_date),
        "province": app.province,
        "city": app.city,
        "district": app.district,
        "accidentType": app.accident_type,
        "injuryType": app.injury_type,
        "insuranceCompany": app.insurance_company,
        "appStatus": app.app_status,
        "caseId": str(app.case_id) if app.case_id else None,
        "rejectRemark": _latest_reject_remark(audits) if app.app_status == APP_STATUS_REJECTED else "",
        "pendingAuditId": str(pending.id) if pending else None,
        "createdAt": _dt_str(app.created_at),
        "updatedAt": _dt_str(app.updated_at),
    }


async def build_application_detail(
    db: AsyncSession,
    application_id: int,
) -> Optional[Dict[str, Any]]:
    app = await db.get(BizCaseApplication, application_id)
    if app is None:
        return None

    stmt = (
        select(BizAuditRecord)
        .where(
            BizAuditRecord.biz_type == BIZ_TYPE_CASE_SUBMIT,
            BizAuditRecord.biz_id == application_id,
        )
        .order_by(BizAuditRecord.submit_batch.asc(), BizAuditRecord.id.asc())
    )
    audits = list((await db.scalars(stmt)).all())
    data = application_list_row(app, audits=audits)
    data["attachments"] = _merge_attachments_from_audits(audits)
    data["policyImages"] = _merge_categorized_materials_from_audits(
        audits,
        structured_field="policyImages",
        category=CASE_MATERIAL_CATEGORY_POLICY,
    )
    data["accidentDecisionImages"] = _merge_categorized_materials_from_audits(
        audits,
        structured_field="accidentDecisionImages",
        category=CASE_MATERIAL_CATEGORY_ACCIDENT_DECISION,
    )
    data["batchHistory"] = [batch_history_item(a) for a in audits]
    return data


async def list_my_applications(
    db: AsyncSession,
    user_id: int,
    *,
    legacy_phone: Optional[str] = None,
) -> List[Dict[str, Any]]:
    phone = (legacy_phone or "").strip()
    if phone:
        stmt = (
            select(BizCaseApplication)
            .where(
                or_(
                    BizCaseApplication.created_by == user_id,
                    (
                        BizCaseApplication.created_by.is_(None)
                        & (BizCaseApplication.victim_phone == phone)
                    ),
                )
            )
            .order_by(BizCaseApplication.updated_at.desc(), BizCaseApplication.id.desc())
        )
    else:
        stmt = (
            select(BizCaseApplication)
            .where(BizCaseApplication.created_by == user_id)
            .order_by(BizCaseApplication.updated_at.desc(), BizCaseApplication.id.desc())
        )
    apps = list((await db.scalars(stmt)).all())
    if not apps:
        return []

    app_ids = [a.id for a in apps]
    audit_stmt = (
        select(BizAuditRecord)
        .where(
            BizAuditRecord.biz_type == BIZ_TYPE_CASE_SUBMIT,
            BizAuditRecord.biz_id.in_(app_ids),
        )
        .order_by(BizAuditRecord.biz_id.asc(), BizAuditRecord.submit_batch.asc())
    )
    audit_rows = list((await db.scalars(audit_stmt)).all())
    audits_by_app: Dict[int, List[BizAuditRecord]] = {aid: [] for aid in app_ids}
    for row in audit_rows:
        audits_by_app.setdefault(int(row.biz_id), []).append(row)

    return [application_list_row(app, audits=audits_by_app.get(app.id, [])) for app in apps]

