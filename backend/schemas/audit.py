from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


VALID_BIZ_TYPES = ("case_submit", "agency_submit", "agency_onboard")
VALID_AUDIT_STATUS = ("pending", "approved", "rejected")


class AuditListQuery(BaseModel):
    pageNum: int = Field(1, ge=1, description="当前页码")
    pageSize: int = Field(10, ge=1, le=200, description="每页条数")
    bizType: Optional[str] = Field(
        None, description="业务类型：case_submit | agency_submit | agency_onboard"
    )
    status: Optional[str] = Field(None, description="审核状态：pending | approved | rejected")


class AuditRejectBody(BaseModel):
    auditRemark: str = Field(..., min_length=1, max_length=500, description="驳回原因")


class CaseSubmitResubmitBody(BaseModel):
    """伤者报案驳回后补件（字段白名单见实施计划 §2.6）"""

    bizType: str = Field("case_submit", description="固定 case_submit")
    bizId: Union[str, int] = Field(..., description="application.id")
    victimName: Optional[str] = Field(None, max_length=50, description="伤者姓名")
    victimPhone: Optional[str] = Field(None, max_length=20, description="联系电话")
    province: Optional[str] = Field(None, max_length=50, description="报案省份")
    city: Optional[str] = Field(None, max_length=50, description="报案城市")
    district: Optional[str] = Field(None, max_length=50, description="报案区县")
    accidentType: Optional[str] = Field(None, max_length=50, description="事故类型")
    injuryType: Optional[str] = Field(None, max_length=50, description="伤情类型")
    policyImages: List[Dict[str, Any]] = Field(default_factory=list, description="本批次新增保单图片")
    accidentDecisionImages: List[Dict[str, Any]] = Field(
        default_factory=list, description="本批次新增事故认定书图片"
    )
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="本批次新增附件（兼容）")


class AgencySubmitResubmitBody(BaseModel):
    """机构报告驳回后重新提交整套文书包"""

    bizType: str = Field("agency_submit", description="固定 agency_submit")
    bizId: Union[str, int] = Field(..., description="case.id")
    documentNumber: str = Field(..., min_length=1, max_length=50, description="鉴定文书编号")
    electronicCertificate: Dict[str, Any] = Field(..., description="电子证书 {name, url}")


class AgencyOnboardResubmitBody(BaseModel):
    """机构入驻驳回后重新提交"""

    bizType: str = Field("agency_onboard", description="固定 agency_onboard")
    bizId: Union[str, int] = Field(..., description="agency.id")
    agencyName: Optional[str] = Field(None, max_length=100)
    contactPerson: Optional[str] = Field(None, max_length=50)
    contactPhone: Optional[str] = Field(None, max_length=20)
    province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=255)
