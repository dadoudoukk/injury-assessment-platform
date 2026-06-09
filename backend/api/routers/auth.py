from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.limiter import limiter
from api.deps import (
    create_access_token,
    get_async_db,
    get_user_perms_bundle,
    make_response,
    pwd_context,
    require_user,
)
from pydantic import BaseModel
from models import SysUser, SysRole
from schemas.system import LoginBody

class WxLoginBody(BaseModel):
    code: str
    phone: Optional[str] = None  # 本地调试降级用的模拟手机号

router = APIRouter(tags=["认证"])


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginBody, db: AsyncSession = Depends(get_async_db)) -> Dict[str, Any]:
    username = body.username.strip()
    user = (await db.scalars(select(SysUser).where(SysUser.username == username, SysUser.is_delete == 0))).first()
    if not user:
        return make_response(500, data={}, msg="用户名或密码错误")
    if not pwd_context.verify(body.password, user.password):
        return make_response(500, data={}, msg="用户名或密码错误")

    token = create_access_token(user.id)
    return make_response(200, data={"access_token": token}, msg="登录成功")


@router.post("/login/wx")
@limiter.limit("5/minute")
async def login_wx(request: Request, body: WxLoginBody, db: AsyncSession = Depends(get_async_db)) -> Dict[str, Any]:
    from core.config import get_settings
    import httpx
    
    settings = get_settings()
    code = body.code.strip()
    
    if not code:
        return make_response(500, data={}, msg="未提供授权 code")
        
    appid = settings.wechat_appid
    secret = settings.wechat_secret
    
    # 如果没配置微信密钥，为了开发方便，允许降级使用前端传的 phone
    if not appid or not secret:
        phone = (body.phone or "").strip()
        if not phone:
            return make_response(500, data={}, msg="后台未配置微信密钥，且未提供模拟手机号")
    else:
        # 正式流程：去微信接口换取手机号
        try:
            async with httpx.AsyncClient() as client:
                # 1. 获取接口调用凭证 access_token
                token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
                token_resp = await client.get(token_url)
                token_data = token_resp.json()
                
                access_token = token_data.get("access_token")
                if not access_token:
                    return make_response(500, data={}, msg=f"微信授权失败(获取token): {token_data.get('errmsg')}")
                
                # 2. 用 code 换取手机号
                phone_url = f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}"
                phone_resp = await client.post(phone_url, json={"code": code})
                phone_data = phone_resp.json()
                
                if phone_data.get("errcode") != 0:
                    return make_response(500, data={}, msg=f"获取手机号失败: {phone_data.get('errmsg')}")
                    
                phone_info = phone_data.get("phone_info", {})
                phone = phone_info.get("phoneNumber") or phone_info.get("purePhoneNumber")
                
                if not phone:
                    return make_response(500, data={}, msg="微信未返回有效手机号")
        except Exception as e:
            return make_response(500, data={}, msg=f"微信接口请求异常: {str(e)}")

    # 根据手机号查找用户
    user = (await db.scalars(select(SysUser).where(SysUser.username == phone, SysUser.is_delete == 0))).first()
    
    if not user:
        # 自动注册为普通伤者账号
        from datetime import datetime
        from models import SysRole
        
        # 查找或创建普通用户角色
        role_stmt = select(SysRole).where(SysRole.name == "普通用户", SysRole.is_delete == 0)
        patient_role = (await db.scalars(role_stmt)).first()
        if not patient_role:
            patient_role = SysRole(
                name="普通用户",
                code="patient",
                description="自动注册的伤者用户角色",
                data_scope=4,  # 仅本人
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(patient_role)
            await db.flush()

        user = SysUser(
            username=phone,
            password=pwd_context.hash("wx123456"), # 随机或默认密码，实际用不到
            nickname=f"用户_{phone[-4:]}",
            phone=phone,
            agency_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        user.roles.append(patient_role)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(user.id)
    return make_response(200, data={"access_token": token, "isPatient": True}, msg="微信授权登录成功")


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
