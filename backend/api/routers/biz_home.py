from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, get_user_perms_bundle, make_response, require_user
from core.context import ctx_agency_id
from core.data_perm import apply_data_scope
from models import AppraisalAgency, BizAuditRecord, CaseRecord
from services.audit_service import (
    AUDIT_STATUS_PENDING,
    BIZ_TYPE_AGENCY_ONBOARD,
    BIZ_TYPE_AGENCY_SUBMIT,
    BIZ_TYPE_CASE_SUBMIT,
    STATUS_PENDING_CONFIRM,
    collect_perm_codes,
)

router = APIRouter(prefix="/biz/home", tags=["业务-工作台"])

_TODO_DEFS = (
    {
        "key": "case_pending_confirm",
        "title": "待确认案件",
        "description": "已派单、待机构确认受理",
        "path": "/caseCenter/pendingConfirm",
        "query": {"statusTab": "1"},
        "perm": "case:edit",
        "countType": "case_status",
        "countStatus": STATUS_PENDING_CONFIRM,
    },
    {
        "key": "case_platform_audit",
        "title": "案件提交审核",
        "description": "伤者小程序新提交待平台审核",
        "path": "/audit/casePlatform",
        "query": {},
        "perm": "case:platformAudit:query",
        "countType": "audit",
        "bizType": BIZ_TYPE_CASE_SUBMIT,
    },
    {
        "key": "case_agency_submit_audit",
        "title": "机构提交审核",
        "description": "鉴定报告/材料待平台审核",
        "path": "/audit/caseAgencySubmit",
        "query": {},
        "perm": "case:agencySubmitAudit:query",
        "countType": "audit",
        "bizType": BIZ_TYPE_AGENCY_SUBMIT,
    },
    {
        "key": "agency_onboard_audit",
        "title": "机构入驻审核",
        "description": "新机构入驻申请待审核",
        "path": "/audit/agencyOnboard",
        "query": {},
        "perm": "agency:audit",
        "countType": "audit",
        "bizType": BIZ_TYPE_AGENCY_ONBOARD,
    },
)


async def _count_case_by_status(db: AsyncSession, status: int) -> int:
    stmt = select(func.count()).select_from(CaseRecord).where(
        CaseRecord.is_delete == 0,
        CaseRecord.status == status,
    )
    stmt = apply_data_scope(stmt, CaseRecord)
    if ctx_agency_id.get() is not None:
        stmt = stmt.where(CaseRecord.agency_id == ctx_agency_id.get())
    return int((await db.scalar(stmt)) or 0)


async def _count_pending_audit(db: AsyncSession, biz_type: str) -> int:
    stmt = select(func.count()).select_from(BizAuditRecord).where(
        BizAuditRecord.biz_type == biz_type,
        BizAuditRecord.status == AUDIT_STATUS_PENDING,
    )
    return int((await db.scalar(stmt)) or 0)


async def _count_legacy_onboard_pending(db: AsyncSession) -> int:
    """无审核记录时回退统计 status=0 的机构（与阶段二双读口径一致）。"""
    audited_ids_stmt = select(BizAuditRecord.biz_id).where(
        BizAuditRecord.biz_type == BIZ_TYPE_AGENCY_ONBOARD,
        BizAuditRecord.status == AUDIT_STATUS_PENDING,
    )
    stmt = select(func.count()).select_from(AppraisalAgency).where(
        AppraisalAgency.is_delete == 0,
        AppraisalAgency.status == 0,
        AppraisalAgency.id.notin_(audited_ids_stmt),
    )
    return int((await db.scalar(stmt)) or 0)


@router.get("/todos")
async def workbench_todos(
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    bundle = await db.run_sync(lambda s: get_user_perms_bundle(s, ctx))
    perm_codes = collect_perm_codes(bundle)

    items: List[Dict[str, Any]] = []
    for definition in _TODO_DEFS:
        perm = definition["perm"]
        if perm not in perm_codes:
            continue

        count = 0
        if definition["countType"] == "case_status":
            count = await _count_case_by_status(db, int(definition["countStatus"]))
        elif definition["countType"] == "audit":
            count = await _count_pending_audit(db, definition["bizType"])
            if definition["bizType"] == BIZ_TYPE_AGENCY_ONBOARD:
                count += await _count_legacy_onboard_pending(db)

        if count <= 0:
            continue

        items.append(
            {
                "key": definition["key"],
                "title": definition["title"],
                "description": definition["description"],
                "count": count,
                "path": definition["path"],
                "query": definition.get("query") or {},
            }
        )

    total = sum(item["count"] for item in items)
    return make_response(200, data={"items": items, "total": total}, msg="success")
