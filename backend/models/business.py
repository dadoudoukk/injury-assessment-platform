from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.base import SoftDeleteMixin


class BizNewsCategory(SoftDeleteMixin, Base):
    """新闻分类表"""

    __tablename__ = "biz_news_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dept_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_dept.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="归属部门（数据权限）",
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人（数据权限-仅本人）",
    )
    category_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True, comment="分类名称")
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")
    status: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="状态：0停用 1启用")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")


class BizNewsArticle(SoftDeleteMixin, Base):
    """新闻文章表"""

    __tablename__ = "biz_news_article"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dept_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_dept.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="归属部门（数据权限）",
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人（数据权限-仅本人）",
    )
    category_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="分类ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="新闻标题")
    author: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="作者")
    news_type: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="类型：0图文内容 1外部跳转")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="正文内容（暂存纯文本）")
    redirect_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="跳转链接")
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="封面图 URL")
    is_top: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="是否置顶：0否 1是")
    status: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="状态：0下架 1发布")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")


class BizFragmentCategory(SoftDeleteMixin, Base):
    """碎片位置表（轮播、金刚区等）"""

    __tablename__ = "biz_fragment_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dept_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_dept.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="归属部门（数据权限）",
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人（数据权限-仅本人）",
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="标识码，如 home_banner")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="位置名称")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")


class BizFragmentContent(SoftDeleteMixin, Base):
    """碎片内容表"""

    __tablename__ = "biz_fragment_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dept_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_dept.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="归属部门（数据权限）",
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人（数据权限-仅本人）",
    )
    category_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="碎片位置 ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="标题")
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="图片链接")
    link_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="跳转链接")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="文本内容")
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")
    status: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="状态：0下线 1上线")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")


class CaseRecord(SoftDeleteMixin, Base):
    """案件记录表"""

    __tablename__ = "biz_case_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dept_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_dept.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="归属部门（数据权限）",
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人（数据权限-仅本人）",
    )
    report_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True, comment="出险报案号"
    )
    victim_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="伤者姓名")
    victim_phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="联系电话")
    city: Mapped[str] = mapped_column(String(50), nullable=False, comment="报案城市")
    district: Mapped[str] = mapped_column(String(50), nullable=False, comment="报案区县")
    status: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, index=True, comment="案件状态：1待接单 2鉴定中 3已完成"
    )
    agency_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="鉴定机构ID")
    insurance_company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="保险公司ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间"
    )
