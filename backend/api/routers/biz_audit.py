from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, get_user_perms_bundle, make_response, require_user
from core.context import ctx_user_id
from schemas.audit import AuditRejectBody, CaseSubmitResubmitBody, VALID_AUDIT_STATUS, VALID_BIZ_TYPES
from services.audit_service import (
    approve_audit,
    approve_perm_for_biz_type,
    can_view_audit_detail,
    collect_perm_codes,
    get_audit_detail,
    list_audit_records,
    reject_audit,
    reject_perm_for_biz_type,
    resubmit_case_submit,
    resolve_list_biz_type_filter,
    _parse_positive_id,
)

router = APIRouter(prefix="/biz/audit", tags=["业务-审核中心"])


async def _load_perm_codes(db: AsyncSession, ctx: dict) -> set[str]:
    bundle = await db.run_sync(lambda s: get_user_perms_bundle(s, ctx))
    return collect_perm_codes(bundle)


@router.get("")
async def audit_list(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200),
    bizType: Optional[str] = Query(None, description="case_submit | agency_submit | agency_onboard"),
    status: Optional[str] = Query(None, description="pending | approved | rejected"),
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    if bizType and bizType not in VALID_BIZ_TYPES:
        return make_response(500, data={}, msg="bizType 参数无效")
    if status and status not in VALID_AUDIT_STATUS:
        return make_response(500, data={}, msg="status 参数无效")

    perm_codes = await _load_perm_codes(db, ctx)
    access_err, allowed_biz_types = resolve_list_biz_type_filter(perm_codes, bizType)
    if access_err:
        raise HTTPException(status_code=403, detail=access_err)

    try:
        rows, total = await list_audit_records(
            db,
            page_num=pageNum,
            page_size=pageSize,
            biz_type=bizType,
            status=status,
            allowed_biz_types=allowed_biz_types,
        )
    except ValueError as exc:
        return make_response(500, data={}, msg=str(exc))

    return make_response(
        200,
        data={"list": rows, "pageNum": pageNum, "pageSize": pageSize, "total": total},
        msg="success",
    )


@router.get("/{audit_id}")
async def audit_detail(
    audit_id: Union[str, int],
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_positive_id(audit_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="审核记录 ID 无效")

    data = await get_audit_detail(db, parsed_id)
    if data is None:
        return make_response(500, data={}, msg="审核记录不存在")

    perm_codes = await _load_perm_codes(db, ctx)
    if not can_view_audit_detail(perm_codes, data.get("bizType")):
        raise HTTPException(status_code=403, detail="无权限访问")

    return make_response(200, data=data, msg="success")


@router.put("/{audit_id}/approve")
async def audit_approve(
    audit_id: Union[str, int],
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_positive_id(audit_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="审核记录 ID 无效")

    detail = await get_audit_detail(db, parsed_id)
    if detail is None:
        return make_response(500, data={}, msg="审核记录不存在")

    biz_type = detail.get("bizType")
    perm_codes = await _load_perm_codes(db, ctx)
    if approve_perm_for_biz_type(biz_type) not in perm_codes:
        raise HTTPException(status_code=403, detail="无权限访问")

    err, suffix = await approve_audit(db, parsed_id, ctx_user_id.get())
    if err:
        return make_response(500, data={}, msg=err)

    msg = "审核通过"
    if suffix:
        msg = f"审核通过{suffix}"
    return make_response(200, data={}, msg=msg)


@router.put("/{audit_id}/reject")
async def audit_reject(
    audit_id: Union[str, int],
    body: AuditRejectBody,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    parsed_id = _parse_positive_id(audit_id)
    if parsed_id is None:
        return make_response(500, data={}, msg="审核记录 ID 无效")

    detail = await get_audit_detail(db, parsed_id)
    if detail is None:
        return make_response(500, data={}, msg="审核记录不存在")

    biz_type = detail.get("bizType")
    perm_codes = await _load_perm_codes(db, ctx)
    if reject_perm_for_biz_type(biz_type) not in perm_codes:
        raise HTTPException(status_code=403, detail="无权限访问")

    remark = body.auditRemark.strip()
    if not remark:
        return make_response(500, data={}, msg="驳回原因不能为空")

    err = await reject_audit(db, parsed_id, remark, ctx_user_id.get())
    if err:
        return make_response(500, data={}, msg=err)

    return make_response(200, data={}, msg="已驳回")


@router.post("/resubmit")
async def audit_resubmit(
    body: CaseSubmitResubmitBody,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    if body.bizType != "case_submit":
        return make_response(500, data={}, msg="当前仅支持 case_submit 补件再提交")

    app_id = _parse_positive_id(body.bizId)
    if app_id is None:
        return make_response(500, data={}, msg="bizId 无效")

    err = await resubmit_case_submit(
        db,
        app_id,
        body.model_dump(exclude_none=True),
        ctx_user_id.get(),
    )
    if err:
        return make_response(500, data={}, msg=err)

    return make_response(200, data={}, msg="补件已提交，请等待平台审核")
