from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.limiter import limiter
from api.deps import (
    create_access_token,
    get_async_db,
    get_user_perms_bundle,
    make_response,
    pwd_context,
    require_user,
)
from api.agency_user import (
    ensure_agency_user_for_login,
    must_change_agency_password,
    resolve_agency_by_phone,
)
from api.wechat_auth import PATIENT_WX_PLACEHOLDER_PASSWORD, resolve_wechat_phone
from pydantic import BaseModel
from models import SysUser, SysRole
from schemas.system import LoginBody

class WxLoginBody(BaseModel):
    code: str
    phone: Optional[str] = None  # 本地调试降级用的模拟手机号

router = APIRouter(tags=["认证"])


def _login_payload(user: SysUser, *, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    token = create_access_token(user.id)
    data: Dict[str, Any] = {"access_token": token}
    if user.agency_id:
        data["mustChangePassword"] = must_change_agency_password(user)
    if extra:
        data.update(extra)
    return data


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginBody, db: AsyncSession = Depends(get_async_db)) -> Dict[str, Any]:
    username = body.username.strip()
    user = (
        await db.scalars(
            select(SysUser)
            .where(SysUser.username == username, SysUser.is_delete == 0)
            .options(selectinload(SysUser.roles))
        )
    ).first()
    if not user:
        return make_response(500, data={}, msg="用户名或密码错误")
    if not pwd_context.verify(body.password, user.password):
        return make_response(500, data={}, msg="用户名或密码错误")
    if not user.is_active:
        return make_response(500, data={}, msg="账号已禁用")

    return make_response(200, data=_login_payload(user), msg="登录成功")


@router.post("/login/wx")
@limiter.limit("5/minute")
async def login_wx(request: Request, body: WxLoginBody, db: AsyncSession = Depends(get_async_db)) -> Dict[str, Any]:
    phone, err = await resolve_wechat_phone(body.code, body.phone)
    if err:
        return make_response(500, data={}, msg=err)

    user = (await db.scalars(select(SysUser).where(SysUser.username == phone, SysUser.is_delete == 0))).first()

    if not user:
        from datetime import datetime

        role_stmt = select(SysRole).where(SysRole.name == "普通用户", SysRole.is_delete == 0)
        patient_role = (await db.scalars(role_stmt)).first()
        if not patient_role:
            patient_role = SysRole(
                name="普通用户",
                code="patient",
                description="自动注册的伤者用户角色",
                data_scope=4,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(patient_role)
            await db.flush()

        user = SysUser(
            username=phone,
            password=pwd_context.hash(PATIENT_WX_PLACEHOLDER_PASSWORD),
            nickname=f"用户_{phone[-4:]}",
            phone=phone,
            agency_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        user.roles.append(patient_role)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(user.id)
    return make_response(200, data={"access_token": token, "isPatient": True}, msg="微信授权登录成功")


@router.post("/login/wx/agency")
@limiter.limit("5/minute")
async def login_wx_agency(
    request: Request,
    body: WxLoginBody,
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    phone, err = await resolve_wechat_phone(body.code, body.phone)
    if err:
        return make_response(500, data={}, msg=err)

    agency, agency_err = await resolve_agency_by_phone(db, phone)
    if agency_err:
        return make_response(500, data={}, msg=agency_err)

    user = await ensure_agency_user_for_login(db, agency)
    if not user:
        return make_response(500, data={}, msg="机构账号初始化失败，请联系平台")
    if not user.is_active:
        return make_response(500, data={}, msg="账号已禁用")

    await db.commit()
    await db.refresh(user)

    return make_response(
        200,
        data=_login_payload(user, extra={"isAgency": True}),
        msg="微信授权登录成功",
    )


@router.post("/logout")
async def logout() -> Dict[str, Any]:
    return make_response(200, data={}, msg="退出成功")


@router.get("/auth/buttons")
async def auth_buttons(
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data={}, msg="登录过期，请重新登录")
    bundle = await db.run_sync(lambda s: get_user_perms_bundle(s, ctx))
    return make_response(200, data=bundle.get("buttonMap") or {}, msg="success")


@router.get("/auth/buttonList")
async def auth_button_list(
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    ctx = await require_user(x_access_token)
    if not ctx:
        return make_response(401, data=[], msg="登录过期，请重新登录")
    bundle = await db.run_sync(lambda s: get_user_perms_bundle(s, ctx))
    return make_response(200, data=bundle.get("codes") or [], msg="success")
