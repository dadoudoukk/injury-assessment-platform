from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
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
        String(50), nullable=False, index=True, comment="出险报案号"
    )
    victim_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="伤者姓名")
    victim_phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="联系电话")
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="出险/报案日期")
    province: Mapped[str] = mapped_column(String(50), nullable=False, comment="报案省份")
    city: Mapped[str] = mapped_column(String(50), nullable=False, comment="报案城市")
    district: Mapped[str] = mapped_column(String(50), nullable=False, comment="报案区县")
    accident_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="事故类型")
    injury_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="伤情类型")
    insurance_company: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="所属保险公司（字典 dict_value，中文名称）"
    )
    status: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        index=True,
        comment="案件状态：1待确认 2已受理 3鉴定中 4已完成 5已打回 6报告待平台审核",
    )
    agency_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="鉴定机构ID")
    rejected_agency_ids: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True, comment="拒单机构 ID 列表 JSON 数组")
    rework_remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="复议打回原因")
    appraisal_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True, comment="鉴定金额/预估理赔款"
    )
    appraisal_conclusion: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="鉴定结论")
    report_files: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True, comment="报告附件 JSON 数组（历史只读）")
    appraisal_videos: Mapped[Optional[List[Any]]] = mapped_column(
        JSON, nullable=True, comment="鉴定取证视频 JSON 数组"
    )
    document_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="鉴定文书编号"
    )
    electronic_certificate: Mapped[Optional[Any]] = mapped_column(
        JSON, nullable=True, comment="电子证书 JSON 对象 {name, url}"
    )
    appraisal_submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="报告提交时间"
    )
    appraisal_submitted_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="报告提交人",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间"
    )


class AppraisalAgency(SoftDeleteMixin, Base):
    """鉴定机构表（平台级主数据，不参与数据权限）"""

    __tablename__ = "biz_appraisal_agency"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agency_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="机构名称"
    )
    contact_person: Mapped[str] = mapped_column(String(50), nullable=False, comment="联系人")
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="联系电话")
    province: Mapped[str] = mapped_column(String(50), nullable=False, comment="省")
    city: Mapped[str] = mapped_column(String(50), nullable=False, comment="市")
    district: Mapped[str] = mapped_column(String(50), nullable=False, comment="区县")
    address: Mapped[str] = mapped_column(String(255), nullable=False, comment="详细地址")
    status: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, index=True, comment="状态：0待审核 1正常 2已停用 3审核驳回"
    )
    audit_remark: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="审核驳回原因"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间"
    )


class BizAgencyServiceScope(Base):
    """鉴定机构合作服务范围（可承接案件的地区，与机构办公地址解耦）"""

    __tablename__ = "biz_agency_service_scope"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agency_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="鉴定机构 ID"
    )
    province: Mapped[str] = mapped_column(String(50), nullable=False, comment="省")
    city: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="市（空表示全省）")
    district: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="区县（空表示全市）")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )


class BizRegionConfig(Base):
    """平台业务开放区域配置（表非空时按白名单启用）"""

    __tablename__ = "biz_region_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    province: Mapped[str] = mapped_column(String(50), nullable=False, comment="省")
    city: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="市（空表示全省）")
    district: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="区县（空表示全市）")
    enabled: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="1启用 0停用")
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="备注")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间"
    )


class BizAgencyRejectLog(Base):
    """机构拒单/换派记录（追加写，用于机构中心拒单记录页）"""

    __tablename__ = "biz_agency_reject_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="案件 ID")
    report_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="出险报案号")
    victim_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="伤者姓名")
    agency_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="被拒/换出机构 ID")
    new_agency_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="换派后新机构 ID，清空时为 NULL"
    )
    rejected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True, comment="拒单/换出时间"
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="操作人",
    )


class BizCaseApplication(Base):
    """伤者报案申请单（审核前主数据，不参与软删除）"""

    __tablename__ = "biz_case_application"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="出险报案号")
    victim_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="伤者姓名")
    victim_phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="联系电话")
    report_date: Mapped[date] = mapped_column(Date, nullable=False, comment="出险/报案日期")
    province: Mapped[str] = mapped_column(String(50), nullable=False, comment="报案省份")
    city: Mapped[str] = mapped_column(String(50), nullable=False, comment="报案城市")
    district: Mapped[str] = mapped_column(String(50), nullable=False, comment="报案区县")
    accident_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="事故类型")
    injury_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="伤情类型")
    insurance_company: Mapped[str] = mapped_column(String(100), nullable=False, comment="所属保险公司")
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="提交人 sys_user.id",
    )
    case_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="审核通过后关联的案件 ID")
    app_status: Mapped[str] = mapped_column(
        String(16),
        default="pending_audit",
        nullable=False,
        comment="pending_audit | rejected | approved",
    )
    is_active: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="1=占用报案号的活跃申请 0=已结案",
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="结案时间")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间"
    )


class BizAuditRecord(Base):
    """统一审核记录"""

    __tablename__ = "biz_audit_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    biz_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="case_submit | agency_submit | agency_onboard"
    )
    biz_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="application.id | case.id | agency.id")
    submit_batch: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="提交批次")
    status: Mapped[str] = mapped_column(
        String(16), default="pending", nullable=False, comment="pending | approved | rejected"
    )
    submit_payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True, comment="本次提交快照")
    audit_remark: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="审核备注/驳回原因")
    audited_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="审核人",
    )
    audited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="审核时间")
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="幂等键")
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="提交人",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间"
    )


class BizInsuranceCompany(SoftDeleteMixin, Base):
    """保险公司表（平台级主数据，不参与数据权限）"""

    __tablename__ = "biz_insurance_company"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="保险公司名称"
    )
    contact_person: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="联系人")
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="联系电话")
    status: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, index=True, comment="状态：1正常 0停用"
    )
    remark: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="备注"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间"
    )
