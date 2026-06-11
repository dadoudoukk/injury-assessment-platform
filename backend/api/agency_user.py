from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import pwd_context
from api.wechat_auth import INITIAL_AGENCY_PASSWORD, PATIENT_WX_PLACEHOLDER_PASSWORD
from models import AppraisalAgency, SysRole, SysUser

# 机构账号若仍为系统占位密码，登录后须强制设置自有密码
_AGENCY_PENDING_PASSWORDS = (INITIAL_AGENCY_PASSWORD, PATIENT_WX_PLACEHOLDER_PASSWORD)


def must_change_agency_password(user: SysUser) -> bool:
    """机构账号仍为系统占位密码（机构初始密或伤者微信占位密）时需强制改密。"""
    if not user.agency_id:
        return False
    for plain in _AGENCY_PENDING_PASSWORDS:
        try:
            if pwd_context.verify(plain, user.password):
                return True
        except Exception:
            continue
    return False


async def get_or_create_agency_role(db: AsyncSession) -> SysRole:
    role_stmt = select(SysRole).where(SysRole.name == "机构管理人员", SysRole.is_delete == 0)
    agency_role = (await db.scalars(role_stmt)).first()
    if agency_role:
        return agency_role

    agency_role = SysRole(
        name="机构管理人员",
        code="agency_admin",
        description="自动创建的机构管理人员角色",
        data_scope=4,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(agency_role)
    await db.flush()
    return agency_role


def _user_has_agency_role(user: SysUser) -> bool:
    for role in user.roles or []:
        if role.code == "agency_admin" or role.name == "机构管理人员":
            return True
    return False


async def bind_agency_admin_user(
    db: AsyncSession,
    agency: AppraisalAgency,
) -> Tuple[str, bool]:
    """
    审核通过时为机构绑定管理员账号。
    若手机号已有账号（如伤者），则升级绑定机构并设为初始密码。
    返回 (提示后缀, 是否新建账号)。
    """
    agency_role = await get_or_create_agency_role(db)
    phone = (agency.contact_phone or "").strip()
    if not phone:
        return "（未填写联系电话，未创建账号）", False

    user_stmt = (
        select(SysUser)
        .where(SysUser.username == phone, SysUser.is_delete == 0)
        .options(selectinload(SysUser.roles))
    )
    existing_user = (await db.scalars(user_stmt)).first()
    now = datetime.utcnow()

    if existing_user:
        existing_user.agency_id = agency.id
        existing_user.phone = phone
        existing_user.nickname = f"{agency.contact_person} (机构管理员)"
        existing_user.password = pwd_context.hash(INITIAL_AGENCY_PASSWORD)
        existing_user.updated_at = now
        if not _user_has_agency_role(existing_user):
            existing_user.roles.append(agency_role)
        return "已关联现有账号，请使用入驻手机号微信登录机构端并设置密码", False

    new_user = SysUser(
        username=phone,
        password=pwd_context.hash(INITIAL_AGENCY_PASSWORD),
        nickname=f"{agency.contact_person} (机构管理员)",
        phone=phone,
        agency_id=agency.id,
        created_at=now,
        updated_at=now,
    )
    new_user.roles.append(agency_role)
    db.add(new_user)
    return "请使用入驻手机号微信登录机构端并设置密码", True


async def resolve_agency_by_phone(db: AsyncSession, phone: str) -> Tuple[Optional[AppraisalAgency], Optional[str]]:
    """按联系电话查找机构并校验状态，返回 (agency, error_msg)。"""
    stmt = select(AppraisalAgency).where(
        AppraisalAgency.contact_phone == phone,
        AppraisalAgency.is_delete == 0,
    )
    agency = (await db.scalars(stmt)).first()
    if agency is None:
        return None, "未找到与该手机号关联的入驻申请，请确认手机号与入驻时填写的一致"

    if agency.status == 0:
        return None, "您的入驻申请正在审核中，请耐心等待"
    if agency.status == 3:
        remark = (agency.audit_remark or "").strip()
        return None, f"您的入驻申请已被驳回{('：' + remark) if remark else ''}"
    if agency.status == 2:
        return None, "机构已停用，请联系平台"
    if agency.status != 1:
        return None, "机构状态异常，请联系平台"

    return agency, None


async def ensure_agency_user_for_login(
    db: AsyncSession,
    agency: AppraisalAgency,
) -> Optional[SysUser]:
    """机构微信登录：确保存在已绑定该机构的用户账号。"""
    phone = (agency.contact_phone or "").strip()
    user_stmt = (
        select(SysUser)
        .where(SysUser.username == phone, SysUser.is_delete == 0)
        .options(selectinload(SysUser.roles))
    )
    user = (await db.scalars(user_stmt)).first()
    if user and user.agency_id == agency.id:
        return user
    if user:
        user.agency_id = agency.id
        agency_role = await get_or_create_agency_role(db)
        if not _user_has_agency_role(user):
            user.roles.append(agency_role)
        user.updated_at = datetime.utcnow()
        await db.flush()
        return user

    agency_role = await get_or_create_agency_role(db)
    now = datetime.utcnow()
    user = SysUser(
        username=phone,
        password=pwd_context.hash(INITIAL_AGENCY_PASSWORD),
        nickname=f"{agency.contact_person} (机构管理员)",
        phone=phone,
        agency_id=agency.id,
        created_at=now,
        updated_at=now,
    )
    user.roles.append(agency_role)
    db.add(user)
    await db.flush()
    return user
