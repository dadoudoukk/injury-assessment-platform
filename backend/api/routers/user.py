from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Set
from urllib.parse import quote

import pandas as pd
from fastapi.concurrency import run_in_threadpool
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import Response

from api.deps import (
    get_async_db,
    get_user_perms_bundle,
    invalidate_user_perms_cache,
    make_response,
    pwd_context,
    require_permission,
    require_user,
)
from api.helpers import (
    gender_to_label,
    gender_to_value,
    safe_cell_to_str,
    user_row,
)
from api.agency_user import must_change_agency_password
from api.wechat_auth import INITIAL_AGENCY_PASSWORD, PATIENT_WX_PLACEHOLDER_PASSWORD
from core.config import get_settings
from models import AppraisalAgency, SysRole, SysUser
from models.rbac import DataScopeEnum
from schemas.user import (
    UserAddBody,
    UserChangePasswordBody,
    UserChangeStatusBody,
    UserDeleteBody,
    UserEditBody,
    UserExportBody,
    UserListBody,
    UserSetInitialPasswordBody,
)

router = APIRouter(prefix="/user", tags=["用户管理"])
_settings = get_settings()


async def _resolve_user_agency_id(db: AsyncSession, agency_id: Optional[int]) -> tuple[Optional[int], Optional[str]]:
    """校验并解析用户绑定的机构 ID；通过返回 (id, None)，失败返回 (None, 错误文案)。"""
    if agency_id is None:
        return None, None
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
        return None, "鉴定机构不存在或不可用"
    return agency_id, None


def _validate_agency_user_roles(agency_id: Optional[int], roles: List[SysRole]) -> Optional[str]:
    """机构账号禁止绑定「全部数据」范围的角色。"""
    if agency_id is None:
        return None
    for role in roles:
        if int(role.data_scope) == DataScopeEnum.ALL.value:
            return "机构账号不可绑定「全部数据」范围的角色"
    return None


def _apply_user_list_filters(
    stmt,
    *,
    username: Optional[str],
    gender: Optional[str],
    agency_id: Optional[int],
    agency_only: Optional[int],
):
    if username and username.strip():
        kw = f"%{username.strip()}%"
        stmt = stmt.where(SysUser.username.like(kw))
    if gender is not None and str(gender).strip() != "":
        stmt = stmt.where(SysUser.gender == str(gender).strip())
    if agency_id is not None:
        stmt = stmt.where(SysUser.agency_id == agency_id)
    if agency_only == 1:
        stmt = stmt.where(SysUser.agency_id.isnot(None))
    return stmt


async def _user_list_perm_codes(db: AsyncSession, ctx: dict) -> Set[str]:
    bundle = await db.run_sync(lambda s: get_user_perms_bundle(s, ctx))
    return set(bundle.get("codes") or [])


def _normalize_user_list_scope(body: UserListBody, perm_codes: Set[str]) -> tuple[UserListBody, Optional[str]]:
    """列表/导出：须具备 user:query；无 user:queryAll 时强制仅查机构账号。"""
    if "user:query" not in perm_codes:
        return body, "无权查询用户列表"
    if "user:queryAll" not in perm_codes:
        return body.model_copy(update={"agencyOnly": 1}), None
    return body, None


def _normalize_user_export_scope(body: UserExportBody, perm_codes: Set[str]) -> tuple[UserExportBody, Optional[str]]:
    if "user:query" not in perm_codes:
        return body, "无权导出用户列表"
    if "user:export" not in perm_codes:
        return body, "无权导出用户列表"
    if "user:queryAll" not in perm_codes:
        return body.model_copy(update={"agencyOnly": 1}), None
    return body, None


@router.get("/info")
async def user_info(
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    bundle = await db.run_sync(lambda s: get_user_perms_bundle(s, ctx))
    buttons = bundle.get("codes") or []

    # Fetch user details to get phone and agency name
    from sqlalchemy.orm import selectinload
    user = (await db.scalars(
        select(SysUser)
        .where(SysUser.id == ctx["user_id"])
        .options(selectinload(SysUser.agency))
    )).first()

    agency = user.agency if user else None
    data = {
        "id": str(ctx["user_id"]),
        "name": ctx["username"],
        "avatar": ctx.get("avatar") or _settings.default_avatar_url,
        "roles": ctx.get("roles") or [],
        "roleName": ctx.get("roleName") or "管理员",
        "agencyId": ctx.get("agency_id"),
        "agencyName": agency.agency_name if agency else None,
        "phone": user.phone if user else None,
        "buttons": buttons,
    }
    if agency:
        data.update(
            {
                "contactPerson": agency.contact_person,
                "contactPhone": agency.contact_phone,
                "province": agency.province,
                "city": agency.city,
                "district": agency.district,
                "address": agency.address,
            }
        )
    if user and user.agency_id:
        data["mustChangePassword"] = must_change_agency_password(user)
    return make_response(200, data=data, msg="success")


@router.post("/changePassword")
async def user_change_password(
    body: UserChangePasswordBody,
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    user = (
        await db.scalars(
            select(SysUser)
            .where(SysUser.id == ctx["user_id"], SysUser.is_delete == 0)
            .options(selectinload(SysUser.roles), selectinload(SysUser.dept))
        )
    ).first()
    if not user:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    if not pwd_context.verify(body.oldPassword, user.password):
        return make_response(500, data={}, msg="原密码不正确")

    user.password = pwd_context.hash(body.newPassword)
    await db.commit()
    return make_response(200, data={}, msg="密码修改成功，请重新登录")


@router.post("/setInitialPassword")
async def user_set_initial_password(
    body: UserSetInitialPasswordBody,
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    user = (
        await db.scalars(
            select(SysUser)
            .where(SysUser.id == ctx["user_id"], SysUser.is_delete == 0)
            .options(selectinload(SysUser.roles), selectinload(SysUser.dept))
        )
    ).first()
    if not user:
        return make_response(401, data={}, msg="登录过期，请重新登录")
    if not user.agency_id:
        return make_response(500, data={}, msg="仅机构账号可设置初始密码")
    if not must_change_agency_password(user):
        return make_response(500, data={}, msg="当前账号无需设置初始密码，请使用修改密码功能")

    new_password = body.newPassword.strip()
    if new_password in (INITIAL_AGENCY_PASSWORD, PATIENT_WX_PLACEHOLDER_PASSWORD):
        return make_response(500, data={}, msg="新密码不能使用系统占位密码")

    user.password = pwd_context.hash(new_password)
    user.updated_at = datetime.utcnow()
    await db.commit()
    return make_response(200, data={}, msg="密码设置成功")


@router.post("/list")
async def user_list_page(
    body: UserListBody,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    perm_codes = await _user_list_perm_codes(db, ctx)
    body, scope_err = _normalize_user_list_scope(body, perm_codes)
    if scope_err:
        return make_response(403, data={}, msg=scope_err)

    q = select(SysUser).where(SysUser.is_delete == 0).options(
        selectinload(SysUser.roles), selectinload(SysUser.dept), selectinload(SysUser.agency)
    )
    q = _apply_user_list_filters(
        q,
        username=body.username,
        gender=body.gender,
        agency_id=body.agencyId,
        agency_only=body.agencyOnly,
    )

    total = (
        await db.scalar(select(func.count()).select_from(SysUser).where(*q._where_criteria))
    ) or 0
    page_num = body.pageNum
    page_size = body.pageSize
    rows = (
        await db.scalars(
            q.order_by(SysUser.id.desc())
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    data = {
        "list": [user_row(u) for u in rows],
        "pageNum": page_num,
        "pageSize": page_size,
        "total": total,
    }
    return make_response(200, data=data, msg="success")


@router.post("/add", dependencies=[Depends(require_permission("user:add"))])
async def user_add(
    body: UserAddBody,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    name = body.username.strip()
    if (await db.scalars(select(SysUser).where(SysUser.username == name, SysUser.is_delete == 0))).first():
        return make_response(500, data={}, msg="用户名已存在")

    gv = (str(body.gender).strip() if body.gender is not None else "") or "3"
    agency_id, agency_err = await _resolve_user_agency_id(db, body.agencyId)
    if agency_err:
        return make_response(500, data={}, msg=agency_err)

    roles: List[SysRole] = []
    if body.roleIds:
        roles = list(
            await db.scalars(
                select(SysRole).where(SysRole.id.in_(body.roleIds), SysRole.is_active == True, SysRole.is_delete == 0)  # noqa: E712
            )
        )
    role_err = _validate_agency_user_roles(agency_id, roles)
    if role_err:
        return make_response(500, data={}, msg=role_err)

    u = SysUser(
        username=name,
        password=pwd_context.hash(body.password),
        nickname=body.nickname,
        email=body.email,
        phone=body.phone,
        gender=gv,
        is_active=True,
        is_superuser=False,
        agency_id=agency_id,
    )
    if roles:
        u.roles = roles
    db.add(u)
    await db.commit()
    invalidate_user_perms_cache(u.id)
    return make_response(200, data={}, msg="新增成功")


@router.post("/delete", dependencies=[Depends(require_permission("user:delete"))])
async def user_delete(
    body: UserDeleteBody,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    current_uid = ctx["user_id"]
    deleted = 0
    for raw in body.id:
        uid = int(raw) if not isinstance(raw, int) else raw
        if uid == current_uid:
            return make_response(500, data={}, msg="不能删除当前登录用户")
        u = (await db.scalars(select(SysUser).where(SysUser.id == uid, SysUser.is_delete == 0))).first()
        if u:
            u.is_delete = 1
            u.delete_time = datetime.now()
            deleted += 1
    if not deleted:
        return make_response(500, data={}, msg="用户不存在或已删除")

    await db.commit()
    for raw in body.id:
        uid = int(raw) if not isinstance(raw, int) else raw
        invalidate_user_perms_cache(uid)
    return make_response(200, data={}, msg="删除成功")


@router.post("/edit", dependencies=[Depends(require_permission("user:edit"))])
async def user_edit(
    body: UserEditBody,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    uid = int(body.id) if not isinstance(body.id, int) else body.id
    u = (
        await db.scalars(
            select(SysUser)
            .where(SysUser.id == uid, SysUser.is_delete == 0)
            .options(selectinload(SysUser.roles), selectinload(SysUser.dept), selectinload(SysUser.agency))
        )
    ).first()
    if not u:
        return make_response(500, data={}, msg="用户不存在")

    if "agencyId" in body.model_fields_set:
        agency_id, agency_err = await _resolve_user_agency_id(db, body.agencyId)
        if agency_err:
            return make_response(500, data={}, msg=agency_err)
        u.agency_id = agency_id

    if body.username is not None:
        name = body.username.strip()
        if not name:
            return make_response(500, data={}, msg="用户名不能为空")
        if name != u.username:
            other = (
                await db.scalars(select(SysUser).where(SysUser.username == name, SysUser.id != uid, SysUser.is_delete == 0))
            ).first()
            if other:
                return make_response(500, data={}, msg="用户名已存在")
            u.username = name

    if body.nickname is not None:
        u.nickname = body.nickname
    if body.email is not None:
        u.email = body.email
    if body.phone is not None:
        u.phone = body.phone
    if body.gender is not None:
        u.gender = str(body.gender).strip() or "3"
    role_ids = list(dict.fromkeys([int(rid) for rid in (body.roleIds or [])]))
    roles: List[SysRole] = []
    if role_ids:
        roles = list(
            await db.scalars(
                select(SysRole).where(SysRole.id.in_(role_ids), SysRole.is_active == True, SysRole.is_delete == 0)  # noqa: E712
            )
        )
        u.roles = roles
    else:
        u.roles = []

    role_err = _validate_agency_user_roles(u.agency_id, roles)
    if role_err:
        return make_response(500, data={}, msg=role_err)

    await db.commit()
    invalidate_user_perms_cache(uid)
    return make_response(200, data={}, msg="编辑成功")


@router.post("/changeStatus")
async def user_change_status(
    body: UserChangeStatusBody,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    if body.status not in (0, 1):
        return make_response(500, data={}, msg="状态参数无效")

    uid = int(body.id) if not isinstance(body.id, int) else body.id
    current_uid = ctx["user_id"]

    if uid == current_uid and body.status == 0:
        return make_response(500, data={}, msg="不能禁用当前登录用户")

    u = (await db.scalars(select(SysUser).where(SysUser.id == uid, SysUser.is_delete == 0))).first()
    if not u:
        return make_response(500, data={}, msg="用户不存在")

    u.is_active = bool(body.status)
    await db.commit()
    invalidate_user_perms_cache(uid)
    return make_response(200, data={}, msg="状态修改成功")


@router.get("/template")
@router.post("/template")
async def user_template_download(
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Response:
    ctx = await require_user(x_access_token)
    if not ctx:
        raise HTTPException(status_code=401, detail="登录过期，请重新登录")

    template_rows = [
        {
            "用户名": "zhangsan",
            "姓名": "张三",
            "性别": "男",
            "手机号": "13800138000",
            "邮箱": "zhangsan@example.com",
            "角色": "普通用户",
        }
    ]
    def _build_template_excel_bytes() -> bytes:
        df = pd.DataFrame(template_rows, columns=["用户名", "姓名", "性别", "手机号", "邮箱", "角色"])
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="用户导入模板")
        return output.getvalue()

    excel_bytes = await run_in_threadpool(_build_template_excel_bytes)
    filename = "用户导入模板.xlsx"
    quoted_name = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename={quoted_name}; filename*=UTF-8''{quoted_name}",
        "Content-Length": str(len(excel_bytes)),
    }
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.post("/export")
async def user_export(
    body: Optional[UserExportBody] = None,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Response:
    ctx = await require_user(x_access_token)
    if not ctx:
        raise HTTPException(status_code=401, detail="登录过期，请重新登录")

    query_body = body or UserExportBody()
    perm_codes = await _user_list_perm_codes(db, ctx)
    query_body, scope_err = _normalize_user_export_scope(query_body, perm_codes)
    if scope_err:
        raise HTTPException(status_code=403, detail=scope_err)

    q = select(SysUser).where(SysUser.is_delete == 0).options(
        selectinload(SysUser.roles), selectinload(SysUser.dept), selectinload(SysUser.agency)
    )
    q = _apply_user_list_filters(
        q,
        username=query_body.username,
        gender=query_body.gender,
        agency_id=query_body.agencyId,
        agency_only=query_body.agencyOnly,
    )
    users = (await db.scalars(q.order_by(SysUser.id.desc()))).all()

    rows: List[Dict[str, Any]] = []
    for u in users:
        role_names = "、".join([r.name for r in (u.roles or []) if (r.name or "").strip()])
        rows.append(
            {
                "用户名": u.username,
                "姓名": u.nickname or "",
                "性别": gender_to_label(u.gender),
                "手机号": u.phone or "",
                "邮箱": u.email or "",
                "所属机构": (u.agency.agency_name if u.agency else "") or "",
                "角色": role_names,
                "状态": "启用" if u.is_active else "禁用",
                "创建时间": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "",
            }
        )

    def _build_export_excel_bytes() -> bytes:
        df = pd.DataFrame(
            rows,
            columns=["用户名", "姓名", "性别", "手机号", "邮箱", "所属机构", "角色", "状态", "创建时间"],
        )
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="用户列表")
        return output.getvalue()

    excel_bytes = await run_in_threadpool(_build_export_excel_bytes)

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"用户列表_{ts}.xlsx"
    quoted_name = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename={quoted_name}; filename*=UTF-8''{quoted_name}",
        "Content-Length": str(len(excel_bytes)),
    }
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.post("/import")
async def user_import(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")

    required_cols = ["用户名", "姓名", "性别", "手机号", "邮箱", "角色"]
    try:
        file_bytes = await file.read()
        dataframe = await run_in_threadpool(lambda: pd.read_excel(BytesIO(file_bytes), engine="openpyxl"))
    except Exception as exc:
        return make_response(500, data={}, msg=f"读取 Excel 失败: {exc}")
    finally:
        await file.close()

    for col in required_cols:
        if col not in dataframe.columns:
            return make_response(500, data={}, msg=f"导入失败，缺少列: {col}")

    role_rows = (
        await db.scalars(select(SysRole).where(SysRole.is_active == True, SysRole.is_delete == 0))  # noqa: E712
    ).all()
    role_map = {r.name.strip(): r for r in role_rows if (r.name or "").strip()}

    success_count = 0
    failed_details: List[str] = []
    pending_users: List[SysUser] = []
    pending_relations: List[tuple[SysUser, List[SysRole]]] = []
    in_batch_usernames: Set[str] = set()

    for idx, row in dataframe.iterrows():
        line_no = idx + 2
        username = safe_cell_to_str(row.get("用户名"))
        nickname = safe_cell_to_str(row.get("姓名"))
        gender = gender_to_value(safe_cell_to_str(row.get("性别")))
        phone = safe_cell_to_str(row.get("手机号"))
        email = safe_cell_to_str(row.get("邮箱"))
        role_raw = safe_cell_to_str(row.get("角色"))

        if not username:
            failed_details.append(f"第{line_no}行: 用户名不能为空")
            continue
        user_exists = (
            await db.scalars(select(SysUser).where(SysUser.username == username, SysUser.is_delete == 0))
        ).first()
        if username in in_batch_usernames or user_exists:
            failed_details.append(f"第{line_no}行: 用户名[{username}]已存在")
            continue

        role_names = [x.strip() for x in role_raw.replace("，", ",").replace("、", ",").split(",") if x.strip()]
        bind_roles = [role_map[rn] for rn in role_names if rn in role_map]
        missing_roles = [rn for rn in role_names if rn not in role_map]
        if missing_roles:
            failed_details.append(f"第{line_no}行: 角色不存在[{','.join(missing_roles)}]")
            continue

        user = SysUser(
            username=username,
            password=pwd_context.hash("123456"),
            nickname=nickname or None,
            email=email or None,
            phone=phone or None,
            gender=gender,
            is_active=True,
            is_superuser=False,
        )
        pending_users.append(user)
        pending_relations.append((user, bind_roles))
        in_batch_usernames.add(username)
        success_count += 1

    if pending_users:
        try:
            for user, roles in pending_relations:
                user.roles = roles
                db.add(user)
            await db.commit()
            for user in pending_users:
                invalidate_user_perms_cache(user.id)
        except Exception as exc:
            await db.rollback()
            return make_response(500, data={}, msg=f"导入失败，数据库写入异常: {exc}")

    fail_count = len(failed_details)
    return make_response(
        200,
        data={
            "successCount": success_count,
            "failCount": fail_count,
            "failReasons": failed_details,
        },
        msg=f"导入完成，成功{success_count}条，失败{fail_count}条",
    )
