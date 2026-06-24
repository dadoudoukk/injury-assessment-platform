"""
一次性初始化脚本：向 MySQL 写入首套 RBAC 基础测试数据。

用法（在 backend 目录下）:
    python init_db.py

也可在项目根目录:
    python backend/init_db.py

数据库连接使用 backend/.env 中的 DATABASE_URL（经 core.config / core.database 加载），请按需修改。
若修改 .env 后仍连错库，先运行: python print_db_config.py（查看环境变量是否覆盖了 .env）。
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 保证从任意工作目录运行都能导入 backend 包
_BACKEND_ROOT = Path(__file__).resolve().parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from passlib.context import CryptContext
from sqlalchemy import false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# 导入模型，确保 metadata 完整
from models import (  # noqa: F401
    BizFragmentCategory,
    BizFragmentContent,
    BizNewsArticle,
    BizNewsCategory,
    CaseRecord,
    SysDept,
    SysDictData,
    SysDictType,
    SysMenu,
    SysApi,
    SysConfig,
    SysOperLog,
    SysRole,
    SysRoleMenu,
    SysUser,
)

from core.database import AsyncSessionLocal, Base, DATABASE_URL, async_engine, sync_engine

# 使用独立同步引擎做建表与 ALTER，勿用 async_engine.sync_engine（aiomysql 下会 MissingGreenlet）
engine = sync_engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def ensure_tables() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_biz_news_article_cover_image_column() -> None:
    """旧库无 cover_image_url 列时执行 ALTER。"""
    from sqlalchemy import inspect, text

    try:
        insp = inspect(engine)
        cols = [c["name"] for c in insp.get_columns("biz_news_article")]
    except Exception:
        return
    if "cover_image_url" in cols:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE biz_news_article ADD COLUMN cover_image_url VARCHAR(512) NULL COMMENT '封面图 URL'"
            )
        )
    print("已为 biz_news_article 表补充 cover_image_url 字段（旧库升级）。")


def _add_column_if_absent(table: str, column: str, sqlite_sql: str, mysql_sql: str) -> None:
    """旧库缺列时执行 ALTER（SQLite / MySQL 各一条 DDL）。"""
    from sqlalchemy import inspect, text

    try:
        insp = inspect(engine)
        cols = [c["name"] for c in insp.get_columns(table)]
    except Exception:
        return
    if column in cols:
        return
    sql = sqlite_sql if DATABASE_URL.startswith("sqlite") else mysql_sql
    with engine.begin() as conn:
        conn.execute(text(sql))
    print(f"已为 {table} 表补充 {column} 字段（旧库升级）。")


def ensure_sys_user_dept_id_column() -> None:
    _add_column_if_absent(
        "sys_user",
        "dept_id",
        "ALTER TABLE sys_user ADD COLUMN dept_id INTEGER NULL",
        "ALTER TABLE sys_user ADD COLUMN dept_id INT NULL COMMENT '归属部门'",
    )


def ensure_sys_user_agency_id_column() -> None:
    _add_column_if_absent(
        "sys_user",
        "agency_id",
        "ALTER TABLE sys_user ADD COLUMN agency_id INTEGER NULL",
        "ALTER TABLE sys_user ADD COLUMN agency_id INT NULL COMMENT '所属鉴定机构，平台用户为 NULL'",
    )


def ensure_sys_role_data_scope_column() -> None:
    _add_column_if_absent(
        "sys_role",
        "data_scope",
        "ALTER TABLE sys_role ADD COLUMN data_scope INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE sys_role ADD COLUMN data_scope INT NOT NULL DEFAULT 1 COMMENT '数据范围 1-5'",
    )


def ensure_biz_news_category_data_perm_columns() -> None:
    _add_column_if_absent(
        "biz_news_category",
        "dept_id",
        "ALTER TABLE biz_news_category ADD COLUMN dept_id INTEGER NULL",
        "ALTER TABLE biz_news_category ADD COLUMN dept_id INT NULL COMMENT '归属部门'",
    )
    _add_column_if_absent(
        "biz_news_category",
        "created_by",
        "ALTER TABLE biz_news_category ADD COLUMN created_by INTEGER NULL",
        "ALTER TABLE biz_news_category ADD COLUMN created_by INT NULL COMMENT '创建人'",
    )


def ensure_biz_news_article_data_perm_columns() -> None:
    _add_column_if_absent(
        "biz_news_article",
        "dept_id",
        "ALTER TABLE biz_news_article ADD COLUMN dept_id INTEGER NULL",
        "ALTER TABLE biz_news_article ADD COLUMN dept_id INT NULL COMMENT '归属部门'",
    )
    _add_column_if_absent(
        "biz_news_article",
        "created_by",
        "ALTER TABLE biz_news_article ADD COLUMN created_by INTEGER NULL",
        "ALTER TABLE biz_news_article ADD COLUMN created_by INT NULL COMMENT '创建人'",
    )


def ensure_biz_fragment_category_data_perm_columns() -> None:
    _add_column_if_absent(
        "biz_fragment_category",
        "dept_id",
        "ALTER TABLE biz_fragment_category ADD COLUMN dept_id INTEGER NULL",
        "ALTER TABLE biz_fragment_category ADD COLUMN dept_id INT NULL COMMENT '归属部门'",
    )
    _add_column_if_absent(
        "biz_fragment_category",
        "created_by",
        "ALTER TABLE biz_fragment_category ADD COLUMN created_by INTEGER NULL",
        "ALTER TABLE biz_fragment_category ADD COLUMN created_by INT NULL COMMENT '创建人'",
    )


def ensure_biz_fragment_content_data_perm_columns() -> None:
    _add_column_if_absent(
        "biz_fragment_content",
        "dept_id",
        "ALTER TABLE biz_fragment_content ADD COLUMN dept_id INTEGER NULL",
        "ALTER TABLE biz_fragment_content ADD COLUMN dept_id INT NULL COMMENT '归属部门'",
    )
    _add_column_if_absent(
        "biz_fragment_content",
        "created_by",
        "ALTER TABLE biz_fragment_content ADD COLUMN created_by INTEGER NULL",
        "ALTER TABLE biz_fragment_content ADD COLUMN created_by INT NULL COMMENT '创建人'",
    )


def ensure_sys_oper_log_request_param_column() -> None:
    """旧库无 request_param 列时执行 ALTER。"""
    from sqlalchemy import inspect, text

    try:
        insp = inspect(engine)
        cols = [c["name"] for c in insp.get_columns("sys_oper_log")]
    except Exception:
        return
    if "request_param" in cols:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE sys_oper_log ADD COLUMN request_param TEXT NULL COMMENT '请求参数'"))
    print("已为 sys_oper_log 表补充 request_param 字段（旧库升级）。")


def ensure_user_gender_column() -> None:
    """旧库无 gender 列时执行 ALTER，避免仅依赖 create_all 无法加列。"""
    from sqlalchemy import inspect, text

    try:
        insp = inspect(engine)
        cols = [c["name"] for c in insp.get_columns("sys_user")]
    except Exception:
        return
    if "gender" in cols:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE sys_user ADD COLUMN gender VARCHAR(8) NOT NULL DEFAULT '3' "
                "COMMENT '字典 sys_user_sex'"
            )
        )
    print("已为 sys_user 表补充 gender 字段（旧库升级）。")


def ensure_sys_menu_api_path_prefix_column() -> None:
    """旧库为 sys_menu 补充 api_path_prefix（接口管理与菜单归属）。"""
    _add_column_if_absent(
        "sys_menu",
        "api_path_prefix",
        "ALTER TABLE sys_menu ADD COLUMN api_path_prefix VARCHAR(512) NULL",
        "ALTER TABLE sys_menu ADD COLUMN api_path_prefix VARCHAR(512) NULL COMMENT '接口路径前缀，逗号分隔'",
    )


def ensure_menu_api_path_prefix_seed(session: Session) -> None:
    """为内置 MENU 回填 api_path_prefix（仅当该字段为空时写入）。"""
    mapping = [
        ("accountManage", "/api/user"),
        ("roleManage", "/api/role"),
        ("menuManage", "/api/menu,/api/auth"),
        ("dictManage", "/api/dict"),
        ("systemLog", "/api/sys/log"),
        ("apiManage", "/api/sys/api"),
        ("fragmentManage", "/api/biz/fragment"),
        ("newsCategory", "/api/biz/newsCategory"),
        ("newsArticle", "/api/biz/newsArticle"),
        ("home", "/api/biz/home"),
    ]
    updated = 0
    for name, prefix in mapping:
        m = session.query(SysMenu).filter(SysMenu.name == name, SysMenu.is_delete == 0).first()
        if m and not (m.api_path_prefix or "").strip():
            m.api_path_prefix = prefix
            updated += 1
    session.commit()
    if updated:
        print(f"已为 {updated} 个菜单补充 api_path_prefix（接口归属映射）。")


def ensure_sys_api_extra_columns() -> None:
    """兼容旧表缺少的 sys_api 字段。"""
    _add_column_if_absent(
        "sys_api",
        "auth_required",
        "ALTER TABLE sys_api ADD COLUMN auth_required BOOLEAN NOT NULL DEFAULT 1",
        "ALTER TABLE sys_api ADD COLUMN auth_required TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否鉴权'",
    )
    _add_column_if_absent(
        "sys_api",
        "log_required",
        "ALTER TABLE sys_api ADD COLUMN log_required BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE sys_api ADD COLUMN log_required TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否记录日志'",
    )
    _add_column_if_absent(
        "sys_api",
        "rate_limit",
        "ALTER TABLE sys_api ADD COLUMN rate_limit INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE sys_api ADD COLUMN rate_limit INT NOT NULL DEFAULT 0 COMMENT '限流QPS'",
    )
    _add_column_if_absent(
        "sys_api",
        "update_time",
        "ALTER TABLE sys_api ADD COLUMN update_time DATETIME NULL",
        "ALTER TABLE sys_api ADD COLUMN update_time DATETIME NULL COMMENT '更新时间'",
    )


def seed(session: Session) -> None:
    if session.query(SysUser).filter(SysUser.username == "admin").first():
        print("已存在用户 admin，跳过写入（避免重复）。")
        return

    menu_home = SysMenu(
        parent_id=None,
        menu_type="MENU",
        name="home",
        title="首页",
        path="/home/index",
        component="/home/index",
        icon="HomeFilled",
        is_affix=True,
        sort=1,
    )
    menu_system = SysMenu(
        parent_id=None,
        menu_type="CATALOG",
        name="system",
        title="系统管理",
        path="/system",
        sort=2,
    )
    session.add_all([menu_home, menu_system])
    session.flush()

    role = SysRole(
        name="超级管理员",
        code="admin",
        description="系统内置超级管理员",
    )
    role.menus = [menu_home, menu_system]
    session.add(role)
    session.flush()

    user = SysUser(
        username="admin",
        password=pwd_context.hash("123456"),
        nickname="管理员",
        gender="3",
        is_superuser=True,
        is_active=True,
    )
    user.roles = [role]
    session.add(user)

    session.commit()
    print("初始化完成：已写入「首页」「系统管理」菜单、超级管理员角色、admin 用户（明文密码 123456）。")


def ensure_user_manage_menu(session: Session) -> None:
    """
    在「系统管理」下挂「用户管理」菜单并授权给 admin 角色；可重复执行（已存在则跳过）。
    """
    parent = session.query(SysMenu).filter(SysMenu.name == "system").first()
    if not parent:
        print("未找到「系统管理」菜单，跳过用户管理菜单补充。")
        return
    if session.query(SysMenu).filter(SysMenu.name == "accountManage").first():
        return

    child = SysMenu(
        parent_id=parent.id,
        menu_type="MENU",
        name="accountManage",
        title="用户管理",
        path="/system/accountManage",
        component="/system/accountManage/index",
        icon="User",
        sort=1,
    )
    session.add(child)
    session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)

    session.commit()
    print("已补充「系统管理 -> 用户管理」菜单并关联超级管理员角色。")


def ensure_role_manage_menu(session: Session) -> None:
    """在「系统管理」下挂「角色管理」菜单并授权给 admin；已存在则跳过。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "system").first()
    if not parent:
        print("未找到「系统管理」菜单，跳过角色管理菜单补充。")
        return
    if session.query(SysMenu).filter(SysMenu.name == "roleManage").first():
        return

    child = SysMenu(
        parent_id=parent.id,
        menu_type="MENU",
        name="roleManage",
        title="角色管理",
        path="/system/roleManage",
        component="/system/roleManage/index",
        icon="UserFilled",
        sort=2,
    )
    session.add(child)
    session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)

    session.commit()
    print("已补充「系统管理 -> 角色管理」菜单并关联超级管理员角色。")


def ensure_menu_manage_menu(session: Session) -> None:
    """在「系统管理」下挂「菜单管理」并授权 admin；已存在则跳过。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "system").first()
    if not parent:
        print("未找到「系统管理」菜单，跳过菜单管理补充。")
        return
    if session.query(SysMenu).filter(SysMenu.name == "menuManage").first():
        return

    child = SysMenu(
        parent_id=parent.id,
        menu_type="MENU",
        name="menuManage",
        title="菜单管理",
        path="/system/menuMange",
        component="/system/menuMange/index",
        icon="Menu",
        sort=3,
    )
    session.add(child)
    session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)

    session.commit()
    print("已补充「系统管理 -> 菜单管理」菜单并关联超级管理员角色。")


def ensure_system_log_menu(session: Session) -> None:
    """在「系统管理」下挂「操作日志」并授权 admin。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "system").first()
    if not parent:
        print("未找到「系统管理」菜单，跳过操作日志菜单补充。")
        return
    child = session.query(SysMenu).filter(SysMenu.name == "systemLog").first()
    if not child:
        child = SysMenu(
            parent_id=parent.id,
            menu_type="MENU",
            name="systemLog",
            title="操作日志",
            path="/system/systemLog",
            component="/system/systemLog/index",
            icon="Document",
            sort=5,
        )
        session.add(child)
        session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)
    session.commit()
    print("已检查「系统管理 -> 操作日志」菜单并关联超级管理员角色。")


def ensure_api_manage_menu(session: Session) -> None:
    """在「系统管理」下挂「接口管理」并授权 admin。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "system").first()
    if not parent:
        print("未找到「系统管理」菜单，跳过接口管理菜单补充。")
        return
    child = session.query(SysMenu).filter(SysMenu.name == "apiManage").first()
    if not child:
        child = SysMenu(
            parent_id=parent.id,
            menu_type="MENU",
            name="apiManage",
            title="接口管理",
            path="/system/apiManage",
            component="/system/apiManage/index",
            icon="Connection",
            sort=6,
        )
        session.add(child)
        session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)
    session.commit()
    print("已检查「系统管理 -> 接口管理」菜单并关联超级管理员角色。")


def ensure_api_docs_iframe_menu(session: Session) -> None:
    """在「系统管理」下挂「接口文档」（内嵌 Swagger），复用前端 iframe 壳组件；已存在则跳过。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "system").first()
    if not parent:
        print("未找到「系统管理」菜单，跳过接口文档菜单补充。")
        return
    if session.query(SysMenu).filter(SysMenu.name == "apiDocs").first():
        return

    child = SysMenu(
        parent_id=parent.id,
        menu_type="MENU",
        name="apiDocs",
        title="接口文档",
        path="/system/apiDocs",
        component="/link/bing/index",
        icon="Document",
        sort=7,
    )
    session.add(child)
    session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)

    session.commit()
    print("已补充「系统管理 -> 接口文档」菜单并关联超级管理员角色。")


def ensure_system_config_menu(session: Session) -> None:
    """在「系统管理」下挂「全局配置」菜单并授权 admin；字段与前端 authMenuList 一致。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "system").first()
    if not parent:
        print("未找到「系统管理」菜单，跳过全局配置菜单补充。")
        return
    child = session.query(SysMenu).filter(SysMenu.name == "systemConfig").first()
    if not child:
        child = SysMenu(
            parent_id=parent.id,
            menu_type="MENU",
            name="systemConfig",
            title="全局配置",
            path="/system/systemConfig",
            component="/system/systemConfig/index",
            icon="Setting",
            sort=55,
        )
        session.add(child)
        session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)
    session.commit()
    print("已检查「系统管理 -> 全局配置」菜单并关联超级管理员角色。")


async def ensure_sys_config(session: AsyncSession) -> None:
    """sys_config 出厂键值：按 config_key 检测，缺则补，可重复执行。"""
    now = datetime.utcnow()
    seeds = (
        ("sys_app_name", "系统名称", "Geeker Admin", "text", "左上角和浏览器标签页标题"),
        ("sys_logo", "系统Logo", "", "image", "左上角系统Logo图片"),
        ("sys_login_captcha", "登录验证码开关", "true", "boolean", "控制登录页是否显示图形验证码"),
    )
    created = 0
    for key, cname, cvalue, ctype, remark in seeds:
        existing = await session.scalar(
            select(SysConfig.id).where(SysConfig.config_key == key, SysConfig.is_delete == 0).limit(1)
        )
        if existing is not None:
            continue
        session.add(
            SysConfig(
                config_name=cname,
                config_key=key,
                config_value=cvalue,
                config_type=ctype,
                remark=remark,
                create_time=now,
                update_time=now,
            )
        )
        created += 1
    if created:
        await session.commit()
        print(f"已写入 sys_config 出厂默认数据（新增 {created} 条）。")
    else:
        print("sys_config 关键项已存在，跳过种子数据。")


def ensure_button_menus_under_parent(
    session: Session,
    parent_menu_name: str,
    definitions: list[tuple[str, str, int]],
) -> None:
    """
    在指定父菜单（name）下批量挂 BUTTON 类型权限节点，并关联 admin 角色。
    以 name 为权限码（与 require_permission / v-auth 一致）；可重复执行。
    """
    parent = session.query(SysMenu).filter(SysMenu.name == parent_menu_name).first()
    if not parent:
        print(f"[按钮权限] 未找到父菜单「{parent_menu_name}」，跳过。")
        return
    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    created = 0
    for code, title, sort in definitions:
        btn = session.query(SysMenu).filter(SysMenu.name == code).first()
        if not btn:
            btn = SysMenu(
                parent_id=parent.id,
                menu_type="BUTTON",
                name=code,
                title=title,
                permission=code,
                sort=sort,
            )
            session.add(btn)
            session.flush()
            created += 1
        elif btn.parent_id != parent.id:
            btn.parent_id = parent.id
        if role and btn not in role.menus:
            role.menus.append(btn)
    session.commit()
    print(f"[按钮权限]「{parent_menu_name}」已同步 {len(definitions)} 个按钮（本批新建 {created} 个）。")


def _ensure_catalog_menu(
    session: Session,
    *,
    name: str,
    title: str,
    path: str,
    icon: str,
    sort: int,
) -> SysMenu:
    """创建或获取一级 CATALOG 菜单。"""
    row = session.query(SysMenu).filter(SysMenu.name == name, SysMenu.is_delete == 0).first()
    if not row:
        row = SysMenu(
            parent_id=None,
            menu_type="CATALOG",
            name=name,
            title=title,
            path=path,
            icon=icon,
            sort=sort,
        )
        session.add(row)
        session.flush()
    else:
        row.title = title
        row.path = path
        row.icon = icon or row.icon
        row.sort = sort
    role = session.query(SysRole).filter(SysRole.code == "admin", SysRole.is_delete == 0).first()
    if role and row not in role.menus:
        role.menus.append(row)
    return row


def _merge_home_menu_names(session: Session) -> None:
    """
    统一首页菜单 name=home，处理 home_index 与 home 并存或重复 home 行。
    保留 id 最小的一条 live home 作为 canonical。
    """
    live_homes = (
        session.query(SysMenu)
        .filter(SysMenu.name == "home", SysMenu.is_delete == 0)
        .order_by(SysMenu.id.asc())
        .all()
    )
    legacy_rows = (
        session.query(SysMenu)
        .filter(SysMenu.name == "home_index", SysMenu.is_delete == 0)
        .order_by(SysMenu.id.asc())
        .all()
    )

    canonical: Optional[SysMenu] = live_homes[0] if live_homes else None

    if canonical is None and legacy_rows:
        canonical = legacy_rows[0]
        canonical.name = "home"
        legacy_rows = legacy_rows[1:]

    if canonical is None:
        return

    def _rebind_role_menus(from_menu_id: int, to_menu_id: int) -> None:
        role_ids = [
            rid
            for (rid,) in session.query(SysRoleMenu.role_id)
            .filter(SysRoleMenu.menu_id == from_menu_id)
            .distinct()
            .all()
        ]
        for role_id in role_ids:
            exists = (
                session.query(SysRoleMenu)
                .filter(SysRoleMenu.role_id == role_id, SysRoleMenu.menu_id == to_menu_id)
                .first()
            )
            if not exists:
                session.add(SysRoleMenu(role_id=role_id, menu_id=to_menu_id))

    for legacy in legacy_rows:
        _rebind_role_menus(legacy.id, canonical.id)
        legacy.is_delete = 1
        legacy.delete_time = datetime.utcnow()

    for dup in live_homes[1:]:
        _rebind_role_menus(dup.id, canonical.id)
        dup.is_delete = 1
        dup.delete_time = datetime.utcnow()

    if not (canonical.api_path_prefix or "").strip():
        canonical.api_path_prefix = "/api/biz/home"


def ensure_phase1_menu_structure(session: Session) -> None:
    """
    阶段一菜单结构：工作台 / 审核中心 / 案件中心 / 机构中心 / 基础资料 / 内容运营。
    可重复执行；与 migrations/phase1_menu_refactor.sql 逻辑一致。
    """
    _merge_home_menu_names(session)

    workbench = _ensure_catalog_menu(
        session, name="workbench", title="工作台", path="/workbench", icon="HomeFilled", sort=1
    )
    audit_center = _ensure_catalog_menu(
        session, name="auditCenter", title="审核中心", path="/audit", icon="CircleCheck", sort=2
    )
    case_center = _ensure_catalog_menu(
        session, name="caseCenter", title="案件中心", path="/case", icon="FolderOpened", sort=3
    )
    agency_center = _ensure_catalog_menu(
        session, name="agencyCenter", title="机构中心", path="/agency", icon="OfficeBuilding", sort=4
    )
    base_data = _ensure_catalog_menu(
        session, name="baseData", title="基础资料", path="/base", icon="Collection", sort=5
    )
    content_ops = _ensure_catalog_menu(
        session, name="contentOps", title="内容运营", path="/content", icon="Reading", sort=6
    )
    system_menu = session.query(SysMenu).filter(SysMenu.name == "system", SysMenu.is_delete == 0).first()
    if system_menu:
        system_menu.sort = 7

    # 首页 → 工作台
    home = (
        session.query(SysMenu)
        .filter(SysMenu.name == "home", SysMenu.is_delete == 0)
        .order_by(SysMenu.id.asc())
        .first()
    )
    if home:
        home.parent_id = workbench.id
        home.sort = 1
        if not (home.api_path_prefix or "").strip():
            home.api_path_prefix = "/api/biz/home"

    # 案件列表
    case_manage = session.query(SysMenu).filter(SysMenu.name == "caseManage", SysMenu.is_delete == 0).first()
    if not case_manage:
        case_manage = SysMenu(
            parent_id=case_center.id,
            menu_type="MENU",
            name="caseManage",
            title="案件列表",
            path="/business/caseManage",
            component="/business/caseManage/index",
            icon="FolderOpened",
            sort=1,
            api_path_prefix="/api/biz/case",
        )
        session.add(case_manage)
        session.flush()
    else:
        case_manage.parent_id = case_center.id
        case_manage.title = "案件列表"
        case_manage.sort = 1
        if not (case_manage.component or "").strip():
            case_manage.component = "/business/caseManage/index"
        if not (case_manage.path or "").strip():
            case_manage.path = "/business/caseManage"
        if not (case_manage.api_path_prefix or "").strip():
            case_manage.api_path_prefix = "/api/biz/case"

    # 鉴定机构档案
    agency_manage = session.query(SysMenu).filter(SysMenu.name == "agencyManage", SysMenu.is_delete == 0).first()
    if not agency_manage:
        agency_manage = SysMenu(
            parent_id=agency_center.id,
            menu_type="MENU",
            name="agencyManage",
            title="鉴定机构档案",
            path="/agency/archive",
            component="/business/agencyManage/index",
            icon="OfficeBuilding",
            sort=1,
            api_path_prefix="/api/biz/agency",
        )
        session.add(agency_manage)
        session.flush()
    else:
        agency_manage.parent_id = agency_center.id
        agency_manage.title = "鉴定机构档案"
        agency_manage.path = "/agency/archive"
        agency_manage.sort = 1
        if not (agency_manage.component or "").strip():
            agency_manage.component = "/business/agencyManage/index"
        if not (agency_manage.api_path_prefix or "").strip():
            agency_manage.api_path_prefix = "/api/biz/agency"

    # 机构入驻审核
    onboard = session.query(SysMenu).filter(SysMenu.name == "agencyOnboardAudit", SysMenu.is_delete == 0).first()
    if not onboard:
        onboard = SysMenu(
            parent_id=audit_center.id,
            menu_type="MENU",
            name="agencyOnboardAudit",
            title="机构入驻审核",
            path="/audit/agencyOnboard",
            component="/audit/agencyOnboard/index",
            icon="CircleCheck",
            sort=3,
            api_path_prefix="/api/biz/audit",
        )
        session.add(onboard)
        session.flush()
    else:
        onboard.parent_id = audit_center.id
        onboard.sort = 3

    role = session.query(SysRole).filter(SysRole.code == "admin", SysRole.is_delete == 0).first()
    if role:
        for m in (case_manage, agency_manage, onboard):
            if m and m not in role.menus:
                role.menus.append(m)

    for child_name, sort in (("insuranceManage", 1), ("fragmentManage", 2)):
        child = session.query(SysMenu).filter(SysMenu.name == child_name, SysMenu.is_delete == 0).first()
        if child:
            child.parent_id = base_data.id
            child.sort = sort

    for child_name, sort in (("newsCategory", 1), ("newsArticle", 2)):
        child = session.query(SysMenu).filter(SysMenu.name == child_name, SysMenu.is_delete == 0).first()
        if child:
            child.parent_id = content_ops.id
            child.sort = sort

    # 软删除 business / newsCenter 空壳
    for obsolete_name in ("business", "newsCenter"):
        obsolete = session.query(SysMenu).filter(SysMenu.name == obsolete_name, SysMenu.is_delete == 0).first()
        if obsolete:
            obsolete.is_delete = 1
            obsolete.delete_time = datetime.utcnow()

    session.commit()
    print("已检查阶段一菜单结构（工作台/审核中心/案件中心/机构中心/基础资料/内容运营）。")


PHASE2_AUDIT_MENU_NAMES = (
    "auditCenter",
    "casePlatformAudit",
    "caseAgencySubmitAudit",
    "agencyOnboardAudit",
    "auditRecord",
)
PHASE2_AUDIT_PERMISSION_CODES = (
    "case:platformAudit:query",
    "case:platformAudit:approve",
    "case:platformAudit:reject",
    "case:agencySubmitAudit:query",
    "case:agencySubmitAudit:approve",
    "case:agencySubmitAudit:reject",
    "auditRecord:query",
)
PHASE2_AUDIT_BUTTON_PARENTS = (
    "casePlatformAudit",
    "caseAgencySubmitAudit",
    "auditRecord",
)


def _find_button_by_permission_or_name(session: Session, code: str) -> Optional[SysMenu]:
    """按 permission 优先、name 兜底查找按钮节点（兼容旧 name 体系）。"""
    code = (code or "").strip()
    if not code:
        return None
    rows = (
        session.query(SysMenu)
        .filter(SysMenu.menu_type == "BUTTON", SysMenu.is_delete == 0)
        .filter(or_(SysMenu.permission == code, SysMenu.name == code))
        .order_by(SysMenu.id.asc())
        .all()
    )
    return rows[0] if rows else None


def _revoke_phase2_audit_from_non_admin(session: Session) -> int:
    """收回非 admin 角色对审核中心菜单/按钮的误授权。"""
    parent_ids = [
        row[0]
        for row in session.query(SysMenu.id)
        .filter(SysMenu.name.in_(PHASE2_AUDIT_BUTTON_PARENTS), SysMenu.is_delete == 0)
        .all()
    ]
    audit_menus = (
        session.query(SysMenu)
        .filter(
            SysMenu.is_delete == 0,
            or_(
                SysMenu.name.in_(PHASE2_AUDIT_MENU_NAMES),
                SysMenu.permission.in_(PHASE2_AUDIT_PERMISSION_CODES),
                SysMenu.parent_id.in_(parent_ids) if parent_ids else false(),
            ),
        )
        .all()
    )
    audit_menu_ids = {m.id for m in audit_menus}
    if not audit_menu_ids:
        return 0

    revoked = 0
    roles = session.query(SysRole).filter(SysRole.code != "admin", SysRole.is_delete == 0).all()
    for role in roles:
        before = len(role.menus)
        role.menus = [m for m in role.menus if m.id not in audit_menu_ids]
        revoked += before - len(role.menus)
    return revoked


def _ensure_audit_buttons_under_parent(
    session: Session,
    parent_menu_name: str,
    definitions: list[tuple[str, str, int]],
) -> tuple[int, int]:
    """审核按钮：permission 优先匹配旧节点，再归位 parent_id。"""
    parent = session.query(SysMenu).filter(SysMenu.name == parent_menu_name, SysMenu.is_delete == 0).first()
    if not parent:
        print(f"[审核按钮] 未找到父菜单「{parent_menu_name}」，跳过。")
        return 0, 0
    role = session.query(SysRole).filter(SysRole.code == "admin", SysRole.is_delete == 0).first()
    created = 0
    reparented = 0
    for code, title, sort in definitions:
        btn = _find_button_by_permission_or_name(session, code)
        if not btn:
            btn = SysMenu(
                parent_id=parent.id,
                menu_type="BUTTON",
                name=code,
                title=title,
                permission=code,
                sort=sort,
            )
            session.add(btn)
            session.flush()
            created += 1
        else:
            if btn.parent_id != parent.id:
                btn.parent_id = parent.id
                reparented += 1
            if not (btn.permission or "").strip():
                btn.permission = code
            btn.title = title
            btn.sort = sort
        if role and btn not in role.menus:
            role.menus.append(btn)
    return created, reparented


def ensure_agency_button_menus(session: Session) -> None:
    """鉴定机构管理页按钮权限。"""
    ensure_button_menus_under_parent(
        session,
        "agencyManage",
        [
            ("agency:add", "新增", 1),
            ("agency:edit", "编辑", 2),
            ("agency:delete", "删除", 3),
            ("agency:audit", "审核", 4),
        ],
    )


def ensure_phase2_audit_menus(session: Session) -> None:
    """
    阶段二 PR-3：审核中心子菜单（案件提交 / 机构提交 / 审核记录）。
    与 migrations/phase2_menu_audit.sql 逻辑一致，可重复执行。
    """
    audit_center = session.query(SysMenu).filter(SysMenu.name == "auditCenter", SysMenu.is_delete == 0).first()
    if not audit_center:
        print("未找到「审核中心」目录，跳过阶段二审核菜单。")
        return

    menu_defs = (
        (
            "casePlatformAudit",
            "案件提交审核",
            "/audit/casePlatform",
            "/audit/casePlatform/index",
            "DocumentChecked",
            1,
            "/api/biz/audit",
        ),
        (
            "caseAgencySubmitAudit",
            "机构提交审核",
            "/audit/caseAgencySubmit",
            "/audit/caseAgencySubmit/index",
            "Tickets",
            2,
            "/api/biz/audit",
        ),
        (
            "auditRecord",
            "审核记录",
            "/audit/record",
            "/audit/record/index",
            "List",
            4,
            "/api/biz/audit",
        ),
    )
    created_menus: list[SysMenu] = []
    for name, title, path, component, icon, sort, api_prefix in menu_defs:
        row = session.query(SysMenu).filter(SysMenu.name == name, SysMenu.is_delete == 0).first()
        if not row:
            row = SysMenu(
                parent_id=audit_center.id,
                menu_type="MENU",
                name=name,
                title=title,
                path=path,
                component=component,
                icon=icon,
                sort=sort,
                api_path_prefix=api_prefix,
            )
            session.add(row)
            session.flush()
            created_menus.append(row)
        else:
            row.parent_id = audit_center.id
            row.title = title
            row.path = path
            row.component = component
            row.icon = icon
            row.sort = sort
            row.api_path_prefix = api_prefix

    onboard = session.query(SysMenu).filter(SysMenu.name == "agencyOnboardAudit", SysMenu.is_delete == 0).first()
    if onboard:
        onboard.parent_id = audit_center.id
        onboard.sort = 3

    role = session.query(SysRole).filter(SysRole.code == "admin", SysRole.is_delete == 0).first()
    if role:
        if audit_center not in role.menus:
            role.menus.append(audit_center)
        for name, *_ in menu_defs:
            menu = session.query(SysMenu).filter(SysMenu.name == name, SysMenu.is_delete == 0).first()
            if menu and menu not in role.menus:
                role.menus.append(menu)
        if onboard and onboard not in role.menus:
            role.menus.append(onboard)

    session.commit()
    print(
        f"已检查阶段二审核菜单（本批新建 {len(created_menus)} 个 MENU）。"
    )


def ensure_phase2_audit_button_menus(session: Session) -> None:
    """阶段二 PR-3：审核中心各页按钮权限（permission 优先归位 + 收回非 admin 误授权）。"""
    total_created = 0
    total_reparented = 0
    for parent_name, definitions in (
        (
            "casePlatformAudit",
            [
                ("case:platformAudit:query", "查询", 0),
                ("case:platformAudit:approve", "通过", 1),
                ("case:platformAudit:reject", "驳回", 2),
            ],
        ),
        (
            "caseAgencySubmitAudit",
            [
                ("case:agencySubmitAudit:query", "查询", 0),
                ("case:agencySubmitAudit:approve", "通过", 1),
                ("case:agencySubmitAudit:reject", "驳回", 2),
            ],
        ),
        (
            "auditRecord",
            [
                ("auditRecord:query", "查询", 0),
            ],
        ),
    ):
        created, reparented = _ensure_audit_buttons_under_parent(session, parent_name, definitions)
        total_created += created
        total_reparented += reparented
    revoked = _revoke_phase2_audit_from_non_admin(session)
    session.commit()
    print(
        f"[审核按钮] 已同步（新建 {total_created}，归位 {total_reparented}，"
        f"收回非 admin 关联 {revoked} 条）。"
    )


def ensure_phase3_experience_menus(session: Session) -> None:
    """阶段三：字典快捷入口、待办提醒、机构账号、拒单记录。"""
    role = session.query(SysRole).filter(SysRole.code == "admin").first()

    base_data = session.query(SysMenu).filter(SysMenu.name == "baseData", SysMenu.is_delete == 0).first()
    if base_data:
        for name, title, path, icon, sort in (
            ("accidentTypeDict", "事故类型", "/base/dict/accidentType", "Warning", 3),
            ("injuryTypeDict", "伤情类型", "/base/dict/injuryType", "FirstAidKit", 4),
        ):
            menu = session.query(SysMenu).filter(SysMenu.name == name, SysMenu.is_delete == 0).first()
            if not menu:
                menu = SysMenu(
                    parent_id=base_data.id,
                    menu_type="MENU",
                    name=name,
                    title=title,
                    path=path,
                    component="/system/dictManage/index",
                    icon=icon,
                    sort=sort,
                    api_path_prefix="/api/dict",
                )
                session.add(menu)
                session.flush()
            else:
                menu.parent_id = base_data.id
                menu.title = title
                menu.path = path
                menu.component = "/system/dictManage/index"
                menu.icon = icon
                menu.sort = sort
                if not (menu.api_path_prefix or "").strip():
                    menu.api_path_prefix = "/api/dict"
            if role:
                if base_data not in role.menus:
                    role.menus.append(base_data)
                if menu not in role.menus:
                    role.menus.append(menu)

    workbench = session.query(SysMenu).filter(SysMenu.name == "workbench", SysMenu.is_delete == 0).first()
    if workbench:
        todo = session.query(SysMenu).filter(SysMenu.name == "workbenchTodo", SysMenu.is_delete == 0).first()
        if not todo:
            todo = SysMenu(
                parent_id=workbench.id,
                menu_type="MENU",
                name="workbenchTodo",
                title="待办提醒",
                path="/workbench/todo",
                component="/workbench/todo/index",
                icon="Bell",
                sort=2,
                api_path_prefix="/api/biz/home",
            )
            session.add(todo)
            session.flush()
        else:
            todo.parent_id = workbench.id
            todo.path = "/workbench/todo"
            todo.component = "/workbench/todo/index"
            todo.sort = 2
            if not (todo.api_path_prefix or "").strip():
                todo.api_path_prefix = "/api/biz/home"
        if role:
            if workbench not in role.menus:
                role.menus.append(workbench)
            if todo not in role.menus:
                role.menus.append(todo)

    agency_center = session.query(SysMenu).filter(SysMenu.name == "agencyCenter", SysMenu.is_delete == 0).first()
    if agency_center:
        agency_menus = (
            ("agencyAccount", "机构账号", "/agency/account", "/system/accountManage/index", "User", 2, "/api/user"),
            (
                "agencyRejectLog",
                "拒单记录",
                "/agency/rejectLog",
                "/business/agencyRejectLog/index",
                "DocumentDelete",
                3,
                "/api/biz/agency",
            ),
        )
        for name, title, path, component, icon, sort, api_prefix in agency_menus:
            menu = session.query(SysMenu).filter(SysMenu.name == name, SysMenu.is_delete == 0).first()
            if not menu:
                menu = SysMenu(
                    parent_id=agency_center.id,
                    menu_type="MENU",
                    name=name,
                    title=title,
                    path=path,
                    component=component,
                    icon=icon,
                    sort=sort,
                    api_path_prefix=api_prefix,
                )
                session.add(menu)
                session.flush()
            else:
                menu.parent_id = agency_center.id
                menu.title = title
                menu.path = path
                menu.component = component
                menu.icon = icon
                menu.sort = sort
                if not (menu.api_path_prefix or "").strip():
                    menu.api_path_prefix = api_prefix
            if role:
                if agency_center not in role.menus:
                    role.menus.append(agency_center)
                if menu not in role.menus:
                    role.menus.append(menu)

    session.commit()
    print("[阶段三] 体验优化菜单已同步。")
    ensure_phase3_button_grants(session)


def _grant_buttons_to_roles_with_page_menus(
    session: Session,
    page_names: tuple[str, ...],
    permission_codes: tuple[str, ...],
) -> int:
    """将已有按钮权限同步给拥有指定页面菜单的角色。"""
    page_ids = [
        row[0]
        for row in session.query(SysMenu.id)
        .filter(SysMenu.name.in_(page_names), SysMenu.is_delete == 0)
        .all()
    ]
    if not page_ids:
        return 0
    role_ids = {
        row[0]
        for row in session.query(SysRoleMenu.role_id).filter(SysRoleMenu.menu_id.in_(page_ids)).distinct().all()
    }
    buttons = (
        session.query(SysMenu)
        .filter(
            SysMenu.menu_type == "BUTTON",
            SysMenu.is_delete == 0,
            SysMenu.permission.in_(permission_codes),
        )
        .all()
    )
    granted = 0
    for role_id in role_ids:
        role = session.query(SysRole).filter(SysRole.id == role_id, SysRole.is_delete == 0).first()
        if not role:
            continue
        for btn in buttons:
            if btn not in role.menus:
                role.menus.append(btn)
                granted += 1
    if granted:
        session.commit()
    return granted


def ensure_user_account_button_menus(session: Session) -> None:
    """系统/机构账号页按钮权限（含列表查询收口）。"""
    ensure_button_menus_under_parent(
        session,
        "accountManage",
        [
            ("user:query", "查询", 0),
            ("user:queryAll", "全量查询", 1),
            ("user:add", "新增", 2),
            ("user:edit", "编辑", 3),
            ("user:delete", "删除", 4),
            ("user:export", "导出", 5),
            ("user:import", "导入", 6),
        ],
    )


def ensure_phase3_button_grants(session: Session) -> None:
    """阶段三：页面菜单与按钮授权对齐（与 phase3_menu_experience.sql 一致）。"""
    ensure_user_account_button_menus(session)
    granted = 0
    granted += _grant_buttons_to_roles_with_page_menus(
        session,
        ("accidentTypeDict", "injuryTypeDict"),
        ("dictData:add", "dictData:edit", "dictData:delete"),
    )
    granted += _grant_buttons_to_roles_with_page_menus(
        session,
        ("agencyAccount",),
        ("user:query", "user:add", "user:edit", "user:delete"),
    )
    granted += _grant_buttons_to_roles_with_page_menus(
        session,
        ("agencyRejectLog",),
        ("agency:query",),
    )
    admin = session.query(SysRole).filter(SysRole.code == "admin", SysRole.is_delete == 0).first()
    if admin:
        for code in ("user:query", "user:queryAll"):
            btn = _find_button_by_permission_or_name(session, code)
            if btn and btn not in admin.menus:
                admin.menus.append(btn)
        session.commit()
    print(f"[阶段三] 按钮授权已同步（角色-按钮新增关联 {granted} 条）。")


def ensure_phase4_completion_menus(session: Session) -> None:
    """阶段四：合作范围、区域配置、入驻审核独立页、案件多视图。"""
    role = session.query(SysRole).filter(SysRole.code == "admin", SysRole.is_delete == 0).first()

    onboard = session.query(SysMenu).filter(SysMenu.name == "agencyOnboardAudit", SysMenu.is_delete == 0).first()
    if onboard:
        onboard.component = "/audit/agencyOnboard/index"
        if not (onboard.api_path_prefix or "").strip():
            onboard.api_path_prefix = "/api/biz/audit"

    agency_center = session.query(SysMenu).filter(SysMenu.name == "agencyCenter", SysMenu.is_delete == 0).first()
    if agency_center:
        scope = session.query(SysMenu).filter(SysMenu.name == "agencyScope", SysMenu.is_delete == 0).first()
        if not scope:
            scope = SysMenu(
                parent_id=agency_center.id,
                menu_type="MENU",
                name="agencyScope",
                title="合作范围",
                path="/agency/scope",
                component="/business/agencyScope/index",
                icon="MapLocation",
                sort=4,
                api_path_prefix="/api/biz/agency",
            )
            session.add(scope)
            session.flush()
        else:
            scope.parent_id = agency_center.id
            scope.path = "/agency/scope"
            scope.component = "/business/agencyScope/index"
            scope.sort = 4
            if not (scope.api_path_prefix or "").strip():
                scope.api_path_prefix = "/api/biz/agency"
        if role:
            if agency_center not in role.menus:
                role.menus.append(agency_center)
            if scope not in role.menus:
                role.menus.append(scope)

    base_data = session.query(SysMenu).filter(SysMenu.name == "baseData", SysMenu.is_delete == 0).first()
    if base_data:
        region = session.query(SysMenu).filter(SysMenu.name == "regionConfig", SysMenu.is_delete == 0).first()
        if not region:
            region = SysMenu(
                parent_id=base_data.id,
                menu_type="MENU",
                name="regionConfig",
                title="区域配置",
                path="/base/regionConfig",
                component="/business/regionConfig/index",
                icon="Place",
                sort=5,
                api_path_prefix="/api/biz/region",
            )
            session.add(region)
            session.flush()
        else:
            region.parent_id = base_data.id
            region.path = "/base/regionConfig"
            region.component = "/business/regionConfig/index"
            region.sort = 5
            if not (region.api_path_prefix or "").strip():
                region.api_path_prefix = "/api/biz/region"
        if role:
            if base_data not in role.menus:
                role.menus.append(base_data)
            if region not in role.menus:
                role.menus.append(region)

    case_center = session.query(SysMenu).filter(SysMenu.name == "caseCenter", SysMenu.is_delete == 0).first()
    if case_center:
        case_views = (
            ("casePendingConfirm", "待确认案件", "/caseCenter/pendingConfirm", "Clock", 2),
            ("caseInProgress", "鉴定中案件", "/caseCenter/inProgress", "Loading", 3),
            ("caseCompleted", "已完成案件", "/caseCenter/completed", "CircleCheck", 4),
            ("caseRework", "已打回案件", "/caseCenter/rework", "RefreshLeft", 5),
        )
        for name, title, path, icon, sort in case_views:
            menu = session.query(SysMenu).filter(SysMenu.name == name, SysMenu.is_delete == 0).first()
            if not menu:
                menu = SysMenu(
                    parent_id=case_center.id,
                    menu_type="MENU",
                    name=name,
                    title=title,
                    path=path,
                    component="/business/caseManage/index",
                    icon=icon,
                    sort=sort,
                    api_path_prefix="/api/biz/case",
                )
                session.add(menu)
                session.flush()
            else:
                menu.parent_id = case_center.id
                menu.title = title
                menu.path = path
                menu.component = "/business/caseManage/index"
                menu.icon = icon
                menu.sort = sort
                if not (menu.api_path_prefix or "").strip():
                    menu.api_path_prefix = "/api/biz/case"
            if role:
                if case_center not in role.menus:
                    role.menus.append(case_center)
                if menu not in role.menus:
                    role.menus.append(menu)

        case_manage = session.query(SysMenu).filter(SysMenu.name == "caseManage", SysMenu.is_delete == 0).first()
        if case_manage:
            case_manage.sort = 1

    session.commit()
    ensure_button_menus_under_parent(
        session,
        "agencyScope",
        [
            ("agency:scope:query", "查询", 0),
            ("agency:scope:edit", "维护", 1),
        ],
    )
    ensure_button_menus_under_parent(
        session,
        "regionConfig",
        [
            ("region:query", "查询", 0),
            ("region:edit", "维护", 1),
        ],
    )
    ensure_button_menus_under_parent(
        session,
        "agencyOnboardAudit",
        [
            ("agency:query", "查询", 0),
            ("agency:audit", "审核", 1),
        ],
    )

    case_manage = session.query(SysMenu).filter(SysMenu.name == "caseManage", SysMenu.is_delete == 0).first()
    if case_manage:
        case_buttons = (
            session.query(SysMenu)
            .filter(SysMenu.parent_id == case_manage.id, SysMenu.menu_type == "BUTTON", SysMenu.is_delete == 0)
            .all()
        )
        for view_name in ("casePendingConfirm", "caseInProgress", "caseCompleted", "caseRework"):
            view_page = session.query(SysMenu).filter(SysMenu.name == view_name, SysMenu.is_delete == 0).first()
            if not view_page:
                continue
            for btn in case_buttons:
                existing = (
                    session.query(SysMenu)
                    .filter(
                        SysMenu.parent_id == view_page.id,
                        SysMenu.permission == btn.permission,
                        SysMenu.menu_type == "BUTTON",
                        SysMenu.is_delete == 0,
                    )
                    .first()
                )
                if existing:
                    continue
                session.add(
                    SysMenu(
                        parent_id=view_page.id,
                        menu_type="BUTTON",
                        name=f"{view_name}_{btn.permission}",
                        title=btn.title,
                        permission=btn.permission,
                        sort=btn.sort,
                    )
                )
        session.flush()

    granted = 0
    granted += _grant_buttons_to_roles_with_page_menus(
        session,
        ("agencyScope",),
        ("agency:scope:query", "agency:scope:edit"),
    )
    granted += _grant_buttons_to_roles_with_page_menus(
        session,
        ("regionConfig",),
        ("region:query", "region:edit"),
    )
    granted += _grant_buttons_to_roles_with_page_menus(
        session,
        ("agencyOnboardAudit",),
        ("agency:query", "agency:audit"),
    )
    case_perms = tuple(
        b.permission
        for b in (
            session.query(SysMenu)
            .filter(
                SysMenu.parent_id == (case_manage.id if case_manage else 0),
                SysMenu.menu_type == "BUTTON",
                SysMenu.is_delete == 0,
            )
            .all()
        )
        if b.permission
    )
    if case_manage and case_perms:
        case_manage_role_ids = {
            row[0]
            for row in session.query(SysRoleMenu.role_id)
            .filter(SysRoleMenu.menu_id == case_manage.id)
            .distinct()
            .all()
        }
        for view_name in ("casePendingConfirm", "caseInProgress", "caseCompleted", "caseRework"):
            view_page = session.query(SysMenu).filter(SysMenu.name == view_name, SysMenu.is_delete == 0).first()
            if not view_page:
                continue
            granted += _grant_buttons_to_roles_with_page_menus(session, (view_name,), case_perms)
            for role_id in case_manage_role_ids:
                role_row = session.query(SysRole).filter(SysRole.id == role_id, SysRole.is_delete == 0).first()
                if role_row and view_page not in role_row.menus:
                    role_row.menus.append(view_page)
    session.commit()
    print(f"[阶段四] 文档剩余功能菜单已同步（按钮授权新增 {granted} 条）。")


def ensure_fragment_manage_menu(session: Session) -> None:
    """「基础资料 -> 碎片管理」菜单并授权 admin。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "baseData", SysMenu.is_delete == 0).first()
    if not parent:
        print("未找到「基础资料」目录，跳过碎片管理菜单。")
        return

    child = session.query(SysMenu).filter(SysMenu.name == "fragmentManage").first()
    if not child:
        child = SysMenu(
            parent_id=parent.id,
            menu_type="MENU",
            name="fragmentManage",
            title="碎片管理",
            path="/business/fragmentManage",
            component="/business/fragmentManage/index",
            icon="PictureFilled",
            sort=1,
        )
        session.add(child)
        session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role:
        if parent not in role.menus:
            role.menus.append(parent)
        if child not in role.menus:
            role.menus.append(child)

    session.commit()
    print("已检查「基础资料 -> 碎片管理」菜单并关联超级管理员角色。")


def ensure_fragment_category_seed(session: Session) -> None:
    """碎片位置初始数据 home_banner。"""
    exists = session.query(BizFragmentCategory).filter(BizFragmentCategory.code == "home_banner").first()
    if exists:
        print("碎片位置 home_banner 已存在，跳过初始化。")
        return
    session.add(BizFragmentCategory(code="home_banner", name="首页轮播图", remark=None))
    session.commit()
    print("已写入碎片位置初始数据：home_banner / 首页轮播图。")


def ensure_fragment_button_menus(session: Session) -> None:
    """碎片管理页的 6 个按钮权限。"""
    ensure_button_menus_under_parent(
        session,
        "fragmentManage",
        [
            ("fragmentCategory:add", "碎片位置-新增", 1),
            ("fragmentCategory:edit", "碎片位置-编辑", 2),
            ("fragmentCategory:delete", "碎片位置-删除", 3),
            ("fragmentContent:add", "碎片内容-新增", 4),
            ("fragmentContent:edit", "碎片内容-编辑", 5),
            ("fragmentContent:delete", "碎片内容-删除", 6),
        ],
    )


def ensure_dict_news_button_menus(session: Session) -> None:
    """字典管理、新闻分类、新闻列表的按钮级权限节点。"""
    ensure_button_menus_under_parent(
        session,
        "dictManage",
        [
            ("dictType:add", "字典类型-新增", 1),
            ("dictType:edit", "字典类型-编辑", 2),
            ("dictType:delete", "字典类型-删除", 3),
            ("dictData:add", "字典数据-新增", 4),
            ("dictData:edit", "字典数据-编辑", 5),
            ("dictData:delete", "字典数据-删除", 6),
        ],
    )
    ensure_button_menus_under_parent(
        session,
        "newsCategory",
        [
            ("newsCategory:add", "新增", 1),
            ("newsCategory:edit", "编辑", 2),
            ("newsCategory:delete", "删除", 3),
        ],
    )
    ensure_button_menus_under_parent(
        session,
        "newsArticle",
        [
            ("newsArticle:add", "新增", 1),
            ("newsArticle:edit", "编辑", 2),
            ("newsArticle:delete", "删除", 3),
        ],
    )


def ensure_role_button_menus(session: Session) -> None:
    """角色管理页按钮权限。"""
    ensure_button_menus_under_parent(
        session,
        "roleManage",
        [
            ("role:add", "角色-新增", 1),
            ("role:edit", "角色-编辑", 2),
            ("role:delete", "角色-删除", 3),
            ("role:auth", "角色-菜单权限", 4),
        ],
    )


def ensure_case_appraisal_button_menu(session: Session) -> None:
    """案件管理：补齐 case:appraisal，并同步授权给已拥有 case:edit 的角色。"""
    ensure_button_menus_under_parent(
        session,
        "caseManage",
        [
            ("case:add", "新增", 1),
            ("case:edit", "编辑", 2),
            ("case:delete", "删除", 3),
            ("case:appraisal", "出具/修改报告", 4),
        ],
    )
    appraisal = session.query(SysMenu).filter(SysMenu.name == "case:appraisal", SysMenu.is_delete == 0).first()
    edit_btn = session.query(SysMenu).filter(SysMenu.name == "case:edit", SysMenu.is_delete == 0).first()
    if not appraisal or not edit_btn:
        return
    role_ids = [
        rid
        for (rid,) in session.query(SysRoleMenu.role_id)
        .filter(SysRoleMenu.menu_id == edit_btn.id)
        .distinct()
        .all()
    ]
    synced = 0
    for role_id in role_ids:
        role = session.query(SysRole).filter(SysRole.id == role_id, SysRole.is_delete == 0).first()
        if role and appraisal not in role.menus:
            role.menus.append(appraisal)
            synced += 1
    session.commit()
    if synced:
        print(f"[按钮权限] 已将 case:appraisal 同步授权给 {synced} 个拥有 case:edit 的角色。")


def ensure_dict_manage_menu(session: Session) -> None:
    """在「系统管理」下挂「字典管理」并授权 admin；已存在则跳过。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "system").first()
    if not parent:
        print("未找到「系统管理」菜单，跳过字典管理补充。")
        return
    if session.query(SysMenu).filter(SysMenu.name == "dictManage").first():
        return

    child = SysMenu(
        parent_id=parent.id,
        menu_type="MENU",
        name="dictManage",
        title="字典管理",
        path="/system/dictManage",
        component="/system/dictManage/index",
        icon="Memo",
        sort=4,
    )
    session.add(child)
    session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)

    session.commit()
    print("已补充「系统管理 -> 字典管理」菜单并关联超级管理员角色。")


def ensure_sys_dict_init(session: Session) -> None:
    """
    写入数据字典「用户性别」测试数据；已存在类型或同编码取值则跳过（可重复执行）。
    """
    code = "sys_user_sex"
    if not session.query(SysDictType).filter(SysDictType.dict_code == code).first():
        session.add(
            SysDictType(
                dict_name="用户性别",
                dict_code=code,
                status=True,
                remark=None,
            )
        )

    items = (
        ("男", "1", 1),
        ("女", "2", 2),
        ("未知", "3", 3),
    )
    for label, value, sort in items:
        exists = (
            session.query(SysDictData)
            .filter(SysDictData.dict_code == code, SysDictData.dict_value == value)
            .first()
        )
        if exists:
            continue
        session.add(
            SysDictData(
                dict_code=code,
                dict_label=label,
                dict_value=value,
                sort=sort,
                status=True,
                remark=None,
            )
        )

    session.commit()
    print("数据字典 sys_user_sex 已检查并写入（无重复项则跳过）。")


def _ensure_dict_type_and_items(
    session: Session,
    *,
    code: str,
    dict_name: str,
    items: tuple[tuple[str, str, int], ...],
    remark: Optional[str] = None,
) -> None:
    """写入字典类型及字典项；类型或同 dict_value 已存在则跳过。"""
    if not session.query(SysDictType).filter(SysDictType.dict_code == code).first():
        session.add(
            SysDictType(
                dict_name=dict_name,
                dict_code=code,
                status=True,
                remark=remark,
            )
        )
    for label, value, sort in items:
        exists = (
            session.query(SysDictData)
            .filter(SysDictData.dict_code == code, SysDictData.dict_value == value)
            .first()
        )
        if exists:
            continue
        session.add(
            SysDictData(
                dict_code=code,
                dict_label=label,
                dict_value=value,
                sort=sort,
                status=True,
                remark=None,
            )
        )


def ensure_biz_case_dict_init(session: Session) -> None:
    """案件管理相关字典（事故类型、伤情类型、保险公司）；可重复执行。"""
    _ensure_dict_type_and_items(
        session,
        code="biz_accident_type",
        dict_name="事故类型",
        items=(
            ("交通事故", "交通事故", 1),
            ("工伤事故", "工伤事故", 2),
            ("意外摔伤", "意外摔伤", 3),
        ),
        remark="案件管理-事故类型",
    )
    _ensure_dict_type_and_items(
        session,
        code="biz_injury_type",
        dict_name="伤情类型",
        items=(
            ("轻微伤", "轻微伤", 1),
            ("轻伤", "轻伤", 2),
            ("重伤", "重伤", 3),
        ),
        remark="案件管理-伤情类型",
    )
    _ensure_dict_type_and_items(
        session,
        code="biz_insurance_company",
        dict_name="保险公司",
        items=(
            ("中国平安", "中国平安", 1),
            ("中国人保", "中国人保", 2),
            ("中国太保", "中国太保", 3),
            ("中国人寿", "中国人寿", 4),
        ),
        remark="案件管理-保险公司（dict_value 存中文名称）",
    )
    session.commit()
    print("案件管理字典 biz_accident_type / biz_injury_type / biz_insurance_company 已检查并写入。")


def ensure_news_center_menu(session: Session) -> None:
    """创建「内容运营 -> 新闻分类」菜单并授权 admin；已存在则跳过。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "contentOps", SysMenu.is_delete == 0).first()
    if not parent:
        parent = _ensure_catalog_menu(
            session, name="contentOps", title="内容运营", path="/content", icon="Reading", sort=6
        )

    child = session.query(SysMenu).filter(SysMenu.name == "newsCategory").first()
    if not child:
        child = SysMenu(
            parent_id=parent.id,
            menu_type="MENU",
            name="newsCategory",
            title="新闻分类",
            path="/news/newsCategory",
            component="/news/newsCategory/index",
            icon="Menu",
            sort=1,
        )
        session.add(child)
        session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role:
        if parent not in role.menus:
            role.menus.append(parent)
        if child not in role.menus:
            role.menus.append(child)

    session.commit()
    print("已检查「内容运营 -> 新闻分类」菜单并关联超级管理员角色。")


def ensure_news_category_init(session: Session) -> None:
    """写入新闻分类初始化数据；已存在同名分类则跳过。"""
    items = [
        ("公司动态", 1),
        ("行业资讯", 2),
        ("通知公告", 3),
    ]
    for name, sort in items:
        exists = session.query(BizNewsCategory).filter(BizNewsCategory.category_name == name).first()
        if exists:
            continue
        session.add(
            BizNewsCategory(
                category_name=name,
                sort=sort,
                status=1,
                remark=None,
            )
        )
    session.commit()
    print("新闻分类初始化数据已检查并写入（无重复项则跳过）。")


def ensure_news_article_menu(session: Session) -> None:
    """在「内容运营」下挂「新闻列表」菜单并授权 admin。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "contentOps", SysMenu.is_delete == 0).first()
    if not parent:
        print("未找到「内容运营」菜单，跳过新闻列表菜单补充。")
        return
    child = session.query(SysMenu).filter(SysMenu.name == "newsArticle").first()
    if not child:
        child = SysMenu(
            parent_id=parent.id,
            menu_type="MENU",
            name="newsArticle",
            title="新闻列表",
            path="/news/newsArticle",
            component="/news/newsArticle/index",
            icon="Document",
            sort=2,
        )
        session.add(child)
        session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)
    session.commit()
    print("已检查「新闻中心 -> 新闻列表」菜单并关联超级管理员角色。")


def ensure_news_article_init(session: Session) -> None:
    """写入一条新闻文章测试数据（挂公司动态分类）。"""
    category = session.query(BizNewsCategory).filter(BizNewsCategory.category_name == "公司动态").first()
    if not category:
        print("未找到「公司动态」分类，跳过新闻文章初始化数据。")
        return

    exists = session.query(BizNewsArticle).filter(BizNewsArticle.title == "欢迎使用新闻中心").first()
    if exists:
        print("新闻文章测试数据已存在，跳过写入。")
        return

    session.add(
        BizNewsArticle(
            category_id=category.id,
            title="欢迎使用新闻中心",
            author="admin",
            news_type=0,
            content="这是一条初始化新闻，用于验证新闻列表基础功能。",
            redirect_url=None,
            is_top=1,
            status=1,
        )
    )
    session.commit()
    print("新闻文章初始化数据已写入。")


def ensure_root_department_and_backfill(session: Session) -> None:
    """默认根部门「总公司」，admin 归属该部门，并回填业务表空的 dept_id / created_by。"""
    root = session.query(SysDept).filter(SysDept.name == "总公司", SysDept.is_delete == 0).first()
    if not root:
        root = SysDept(parent_id=None, name="总公司", sort=0, status=1, remark="数据权限默认根部门")
        session.add(root)
        session.flush()

    admin = session.query(SysUser).filter(SysUser.username == "admin").first()
    if admin and admin.dept_id is None:
        admin.dept_id = root.id

    aid = admin.id if admin else None
    did = root.id
    if aid and did:
        for model in (BizNewsCategory, BizNewsArticle, BizFragmentCategory, BizFragmentContent):
            for row in session.query(model).all():
                if getattr(row, "dept_id", None) is None:
                    row.dept_id = did
                if getattr(row, "created_by", None) is None:
                    row.created_by = aid
    session.commit()
    print("已检查默认部门「总公司」、admin 部门归属及业务表数据权限字段回填。")


def ensure_insurance_manage_menu(session: Session) -> None:
    """在「基础资料」下挂「保险公司」并授权 admin。"""
    parent = session.query(SysMenu).filter(SysMenu.name == "baseData", SysMenu.is_delete == 0).first()
    if not parent:
        print("未找到「基础资料」菜单，跳过保险公司菜单补充。")
        return
    child = session.query(SysMenu).filter(SysMenu.name == "insuranceManage").first()
    if not child:
        child = SysMenu(
            parent_id=parent.id,
            menu_type="MENU",
            name="insuranceManage",
            title="保险公司管理",
            path="/business/insuranceManage",
            component="/business/insuranceManage/index",
            icon="Menu",
            sort=6,
        )
        session.add(child)
        session.flush()

    role = session.query(SysRole).filter(SysRole.code == "admin").first()
    if role and child not in role.menus:
        role.menus.append(child)
    session.commit()
    print("已检查「基础资料 -> 保险公司管理」菜单并关联超级管理员角色。")

def ensure_insurance_button_menus(session: Session) -> None:
    """保险公司页的按钮权限。"""
    ensure_button_menus_under_parent(
        session,
        "insuranceManage",
        [
            ("insurance:query", "查询", 1),
            ("insurance:add", "新增", 2),
            ("insurance:edit", "编辑", 3),
            ("insurance:delete", "删除", 4),
        ],
    )

def ensure_insurance_init_data(session: Session) -> None:
    from models.business import BizInsuranceCompany
    from models.dictionary import SysDictData
    
    existing = session.query(BizInsuranceCompany).first()
    if existing:
        return
        
    dict_items = session.query(SysDictData).filter(SysDictData.dict_code == "biz_insurance_company", SysDictData.status == 1).all()
    for item in dict_items:
        session.add(BizInsuranceCompany(
            company_name=item.dict_label,
            status=1,
            remark="来自字典迁移"
        ))
    session.commit()
    print("已将 biz_insurance_company 字典数据迁移到实体表。")

def ensure_case_record_rejected_agencies_column() -> None:
    from sqlalchemy import inspect, text

    try:
        insp = inspect(engine)
        cols = [c["name"] for c in insp.get_columns("biz_case_record")]
    except Exception:
        return
    if "rejected_agency_ids" in cols:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE biz_case_record ADD COLUMN rejected_agency_ids JSON NULL COMMENT '拒单机构 ID 列表 JSON 数组'"
            )
        )
    print("已为 biz_case_record 表补充 rejected_agency_ids 字段。")

def ensure_case_record_rework_remark_column() -> None:
    from sqlalchemy import inspect, text

    try:
        insp = inspect(engine)
        cols = [c["name"] for c in insp.get_columns("biz_case_record")]
    except Exception:
        return
    if "rework_remark" not in cols:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE biz_case_record ADD COLUMN rework_remark VARCHAR(255) NULL COMMENT '复议打回原因'"
                )
            )
        print("已为 biz_case_record 表补充 rework_remark 字段。")


def ensure_case_record_appraisal_flow_columns() -> None:
    from sqlalchemy import inspect, text

    try:
        insp = inspect(engine)
        cols = [c["name"] for c in insp.get_columns("biz_case_record")]
    except Exception:
        return
    alters: list[str] = []
    if "appraisal_videos" not in cols:
        alters.append(
            "ALTER TABLE biz_case_record ADD COLUMN appraisal_videos JSON NULL COMMENT '鉴定取证视频 JSON 数组'"
        )
    if "document_number" not in cols:
        alters.append(
            "ALTER TABLE biz_case_record ADD COLUMN document_number VARCHAR(50) NULL COMMENT '鉴定文书编号'"
        )
    if "electronic_certificate" not in cols:
        alters.append(
            "ALTER TABLE biz_case_record ADD COLUMN electronic_certificate JSON NULL COMMENT '电子证书 JSON 对象 {name, url}'"
        )
    if not alters:
        return
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))
    print("已为 biz_case_record 表补充 appraisal_videos / document_number / electronic_certificate 字段。")


async def main() -> None:
    try:
        ensure_tables()
        ensure_user_gender_column()
        ensure_biz_news_article_cover_image_column()
        ensure_sys_oper_log_request_param_column()
        ensure_sys_user_dept_id_column()
        ensure_sys_user_agency_id_column()
        ensure_sys_role_data_scope_column()
        ensure_biz_news_category_data_perm_columns()
        ensure_biz_news_article_data_perm_columns()
        ensure_biz_fragment_category_data_perm_columns()
        ensure_biz_fragment_content_data_perm_columns()
        ensure_sys_api_extra_columns()
        ensure_sys_menu_api_path_prefix_column()
        ensure_case_record_rejected_agencies_column()
        ensure_case_record_rework_remark_column()
        ensure_case_record_appraisal_flow_columns()
        async with AsyncSessionLocal() as session:
            try:
                await session.run_sync(seed)
                await session.run_sync(ensure_user_manage_menu)
                await session.run_sync(ensure_role_manage_menu)
                await session.run_sync(ensure_menu_manage_menu)
                await session.run_sync(ensure_system_log_menu)
                await session.run_sync(ensure_api_manage_menu)
                await session.run_sync(ensure_api_docs_iframe_menu)
                await session.run_sync(ensure_system_config_menu)
                await ensure_sys_config(session)
                await session.run_sync(ensure_menu_api_path_prefix_seed)
                await session.run_sync(ensure_dict_manage_menu)
                await session.run_sync(ensure_sys_dict_init)
                await session.run_sync(ensure_biz_case_dict_init)
                await session.run_sync(ensure_news_center_menu)
                await session.run_sync(ensure_news_category_init)
                await session.run_sync(ensure_news_article_menu)
                await session.run_sync(ensure_news_article_init)
                await session.run_sync(ensure_phase1_menu_structure)
                await session.run_sync(ensure_fragment_manage_menu)
                await session.run_sync(ensure_fragment_category_seed)
                await session.run_sync(ensure_dict_news_button_menus)
                await session.run_sync(ensure_role_button_menus)
                await session.run_sync(ensure_case_appraisal_button_menu)
                await session.run_sync(ensure_agency_button_menus)
                await session.run_sync(ensure_phase2_audit_menus)
                await session.run_sync(ensure_phase2_audit_button_menus)
                await session.run_sync(ensure_phase3_experience_menus)
                await session.run_sync(ensure_phase4_completion_menus)
                await session.run_sync(ensure_fragment_button_menus)
                await session.run_sync(ensure_root_department_and_backfill)
                await session.run_sync(ensure_insurance_manage_menu)
                await session.run_sync(ensure_insurance_button_menus)
                await session.run_sync(ensure_insurance_init_data)
            except Exception:
                await session.rollback()
                raise
    finally:
        # Windows 下若不显式 dispose，aiomysql 连接对象可能在事件循环关闭后才析构，出现噪音告警。
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
