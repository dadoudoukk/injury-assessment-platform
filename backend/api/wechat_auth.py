from __future__ import annotations

from typing import Optional, Tuple

import httpx

from core.config import get_settings

INITIAL_AGENCY_PASSWORD = "123456"
PATIENT_WX_PLACEHOLDER_PASSWORD = "wx123456"


async def resolve_wechat_phone(code: str, fallback_phone: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """用微信 code 换取手机号；未配置密钥时降级使用 fallback_phone。返回 (phone, error_msg)。"""
    code = (code or "").strip()
    if not code:
        return None, "未提供授权 code"

    settings = get_settings()
    appid = settings.wechat_appid
    secret = settings.wechat_secret

    if not appid or not secret:
        phone = (fallback_phone or "").strip()
        if not phone:
            return None, "后台未配置微信密钥，且未提供模拟手机号"
        return phone, None

    try:
        async with httpx.AsyncClient() as client:
            token_url = (
                f"https://api.weixin.qq.com/cgi-bin/token"
                f"?grant_type=client_credential&appid={appid}&secret={secret}"
            )
            token_resp = await client.get(token_url)
            token_data = token_resp.json()

            access_token = token_data.get("access_token")
            if not access_token:
                return None, f"微信授权失败(获取token): {token_data.get('errmsg')}"

            phone_url = (
                f"https://api.weixin.qq.com/wxa/business/getuserphonenumber"
                f"?access_token={access_token}"
            )
            phone_resp = await client.post(phone_url, json={"code": code})
            phone_data = phone_resp.json()

            if phone_data.get("errcode") != 0:
                return None, f"获取手机号失败: {phone_data.get('errmsg')}"

            phone_info = phone_data.get("phone_info", {})
            phone = phone_info.get("phoneNumber") or phone_info.get("purePhoneNumber")
            if not phone:
                return None, "微信未返回有效手机号"
            return phone, None
    except Exception as exc:
        return None, f"微信接口请求异常: {str(exc)}"
