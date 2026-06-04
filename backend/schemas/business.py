from datetime import date
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class NewsCategoryListBody(BaseModel):
    pageNum: int = Field(1, ge=1, description="当前页码")
    pageSize: int = Field(10, ge=1, le=200, description="每页条数")
    categoryName: Optional[str] = Field(None, description="分类名称模糊搜索")


class NewsCategoryAddBody(BaseModel):
    categoryName: str = Field(..., min_length=1, description="分类名称")
    sort: int = Field(0, description="排序")
    status: int = Field(1, description="状态：0停用 1启用")
    remark: Optional[str] = Field(None, description="备注")


class NewsCategoryEditBody(BaseModel):
    id: Union[str, int] = Field(..., description="分类 ID")
    categoryName: str = Field(..., min_length=1, description="分类名称")
    sort: int = Field(0, description="排序")
    status: int = Field(1, description="状态：0停用 1启用")
    remark: Optional[str] = Field(None, description="备注")


class NewsCategoryDeleteBody(BaseModel):
    id: List[Union[str, int]] = Field(..., min_length=1, description="待删除分类 ID 列表")


class NewsCategoryChangeStatusBody(BaseModel):
    id: Union[str, int] = Field(..., description="分类 ID")
    status: int = Field(..., description="状态：0停用 1启用")


class NewsArticleListBody(BaseModel):
    pageNum: int = Field(1, ge=1, description="当前页码")
    pageSize: int = Field(10, ge=1, le=200, description="每页条数")
    title: Optional[str] = Field(None, description="标题模糊搜索")
    categoryId: Optional[Union[str, int]] = Field(None, description="分类 ID")


class NewsArticleAddBody(BaseModel):
    categoryId: Union[str, int] = Field(..., description="分类 ID")
    title: str = Field(..., min_length=1, description="新闻标题")
    author: Optional[str] = Field(None, description="作者")
    newsType: int = Field(0, description="类型：0图文内容 1外部跳转")
    content: Optional[str] = Field(None, description="正文内容")
    redirectUrl: Optional[str] = Field(None, description="跳转链接")
    imageUrl: Optional[str] = Field(None, description="封面图 URL")
    isTop: int = Field(0, description="是否置顶：0否 1是")
    status: int = Field(1, description="状态：0下架 1发布")


class NewsArticleEditBody(BaseModel):
    id: Union[str, int] = Field(..., description="文章 ID")
    categoryId: Union[str, int] = Field(..., description="分类 ID")
    title: str = Field(..., min_length=1, description="新闻标题")
    author: Optional[str] = Field(None, description="作者")
    newsType: int = Field(0, description="类型：0图文内容 1外部跳转")
    content: Optional[str] = Field(None, description="正文内容")
    redirectUrl: Optional[str] = Field(None, description="跳转链接")
    imageUrl: Optional[str] = Field(None, description="封面图 URL")
    isTop: int = Field(0, description="是否置顶：0否 1是")
    status: int = Field(1, description="状态：0下架 1发布")


class NewsArticleDeleteBody(BaseModel):
    id: List[Union[str, int]] = Field(..., min_length=1, description="待删除文章 ID 列表")


class NewsArticleChangeStatusBody(BaseModel):
    id: Union[str, int] = Field(..., description="文章 ID")
    status: int = Field(..., description="状态：0下架 1发布")


class FragmentCategoryListBody(BaseModel):
    pageNum: int = Field(1, ge=1, description="当前页码")
    pageSize: int = Field(10, ge=1, le=200, description="每页条数")
    code: Optional[str] = Field(None, description="标识码模糊搜索")
    name: Optional[str] = Field(None, description="位置名称模糊搜索")


class FragmentCategoryAddBody(BaseModel):
    code: str = Field(..., min_length=1, description="标识码")
    name: str = Field(..., min_length=1, description="位置名称")
    remark: Optional[str] = Field(None, description="备注")


class FragmentCategoryEditBody(BaseModel):
    id: Union[str, int] = Field(..., description="位置 ID")
    code: str = Field(..., min_length=1, description="标识码")
    name: str = Field(..., min_length=1, description="位置名称")
    remark: Optional[str] = Field(None, description="备注")


class FragmentCategoryDeleteBody(BaseModel):
    id: List[Union[str, int]] = Field(..., min_length=1, description="待删除位置 ID 列表")


class FragmentContentListBody(BaseModel):
    pageNum: int = Field(1, ge=1, description="当前页码")
    pageSize: int = Field(10, ge=1, le=200, description="每页条数")
    categoryId: Optional[Union[str, int]] = Field(None, description="碎片位置 ID，筛选")
    title: Optional[str] = Field(None, description="标题模糊搜索")


class FragmentContentAddBody(BaseModel):
    categoryId: Union[str, int] = Field(..., description="碎片位置 ID")
    title: str = Field(..., min_length=1, description="标题")
    imageUrl: Optional[str] = Field(None, description="图片链接")
    linkUrl: Optional[str] = Field(None, description="跳转链接")
    content: Optional[str] = Field(None, description="文本内容")
    sort: int = Field(0, description="排序")
    status: int = Field(1, description="状态：0下线 1上线")


class FragmentContentEditBody(BaseModel):
    id: Union[str, int] = Field(..., description="内容 ID")
    title: str = Field(..., min_length=1, description="标题")
    imageUrl: Optional[str] = Field(None, description="图片链接")
    linkUrl: Optional[str] = Field(None, description="跳转链接")
    content: Optional[str] = Field(None, description="文本内容")
    sort: int = Field(0, description="排序")
    status: int = Field(1, description="状态：0下线 1上线")


class FragmentContentDeleteBody(BaseModel):
    id: List[Union[str, int]] = Field(..., min_length=1, description="待删除内容 ID 列表")


class FragmentContentChangeStatusBody(BaseModel):
    id: Union[str, int] = Field(..., description="内容 ID")
    status: int = Field(..., description="状态：0下线 1上线")


class CaseRecordListQuery(BaseModel):
    pageNum: int = Field(1, ge=1, description="当前页码")
    pageSize: int = Field(10, ge=1, le=200, description="每页条数")
    reportNumber: Optional[str] = Field(None, description="出险报案号模糊搜索")
    victimName: Optional[str] = Field(None, description="伤者姓名模糊搜索")
    status: Optional[int] = Field(None, description="案件状态：1待接单 2鉴定中 3已完成")
    insuranceCompany: Optional[str] = Field(None, description="所属保险公司（精确匹配，中文名称）")
    reportDateStart: Optional[date] = Field(None, description="报案日期起（含）")
    reportDateEnd: Optional[date] = Field(None, description="报案日期止（含）")


class CaseRecordCreate(BaseModel):
    reportNumber: str = Field(..., min_length=1, max_length=50, description="出险报案号")
    victimName: str = Field(..., min_length=1, max_length=50, description="伤者姓名")
    victimPhone: str = Field(..., min_length=1, max_length=20, description="联系电话")
    reportDate: date = Field(..., description="出险/报案日期 YYYY-MM-DD")
    province: str = Field(..., min_length=1, max_length=50, description="报案省份")
    city: str = Field(..., min_length=1, max_length=50, description="报案城市")
    district: str = Field(..., min_length=1, max_length=50, description="报案区县")
    accidentType: str = Field(..., min_length=1, max_length=50, description="事故类型")
    injuryType: str = Field(..., min_length=1, max_length=50, description="伤情类型")
    insuranceCompany: str = Field(..., min_length=1, max_length=100, description="所属保险公司")
    status: int = Field(1, description="案件状态：1待接单 2鉴定中 3已完成")
    agencyId: Optional[int] = Field(None, description="鉴定机构ID")


class CaseRecordUpdate(BaseModel):
    reportNumber: Optional[str] = Field(None, min_length=1, max_length=50, description="出险报案号")
    victimName: Optional[str] = Field(None, min_length=1, max_length=50, description="伤者姓名")
    victimPhone: Optional[str] = Field(None, min_length=1, max_length=20, description="联系电话")
    reportDate: Optional[date] = Field(None, description="出险/报案日期 YYYY-MM-DD")
    province: Optional[str] = Field(None, min_length=1, max_length=50, description="报案省份")
    city: Optional[str] = Field(None, min_length=1, max_length=50, description="报案城市")
    district: Optional[str] = Field(None, min_length=1, max_length=50, description="报案区县")
    accidentType: Optional[str] = Field(None, min_length=1, max_length=50, description="事故类型")
    injuryType: Optional[str] = Field(None, min_length=1, max_length=50, description="伤情类型")
    insuranceCompany: Optional[str] = Field(None, min_length=1, max_length=100, description="所属保险公司")
    status: Optional[int] = Field(None, description="案件状态：1待接单 2鉴定中 3已完成")
    agencyId: Optional[int] = Field(None, description="鉴定机构ID")


class CaseRecordOut(BaseModel):
    id: str
    reportNumber: str
    victimName: str
    victimPhone: str
    reportDate: str
    province: str
    city: str
    district: str
    accidentType: str
    injuryType: str
    insuranceCompany: str
    status: int
    agencyId: Optional[int] = None
    createdAt: str
    updatedAt: str


class AppraisalAgencyListQuery(BaseModel):
    pageNum: int = Field(1, ge=1, description="当前页码")
    pageSize: int = Field(10, ge=1, le=200, description="每页条数")
    agencyName: Optional[str] = Field(None, description="机构名称模糊搜索")
    contactPerson: Optional[str] = Field(None, description="联系人模糊搜索")
    status: Optional[int] = Field(None, description="状态：0待审核 1正常 2已停用 3审核驳回")
    province: Optional[str] = Field(None, description="省（精确匹配）")
    city: Optional[str] = Field(None, description="市（精确匹配）")
    district: Optional[str] = Field(None, description="区县（精确匹配）")


class AppraisalAgencyCreate(BaseModel):
    agencyName: str = Field(..., min_length=1, max_length=100, description="机构名称")
    contactPerson: str = Field(..., min_length=1, max_length=50, description="联系人")
    contactPhone: str = Field(..., min_length=1, max_length=20, description="联系电话")
    province: str = Field(..., min_length=1, max_length=50, description="省")
    city: str = Field(..., min_length=1, max_length=50, description="市")
    district: str = Field(..., min_length=1, max_length=50, description="区县")
    address: str = Field(..., min_length=1, max_length=255, description="详细地址")


class AppraisalAgencyUpdate(BaseModel):
    agencyName: Optional[str] = Field(None, min_length=1, max_length=100, description="机构名称")
    contactPerson: Optional[str] = Field(None, min_length=1, max_length=50, description="联系人")
    contactPhone: Optional[str] = Field(None, min_length=1, max_length=20, description="联系电话")
    province: Optional[str] = Field(None, min_length=1, max_length=50, description="省")
    city: Optional[str] = Field(None, min_length=1, max_length=50, description="市")
    district: Optional[str] = Field(None, min_length=1, max_length=50, description="区县")
    address: Optional[str] = Field(None, min_length=1, max_length=255, description="详细地址")


class AppraisalAgencyAudit(BaseModel):
    status: int = Field(..., description="审核结果：1通过 3驳回")
    auditRemark: Optional[str] = Field(None, max_length=255, description="驳回原因（status=3 时必填）")


class AppraisalAgencyOut(BaseModel):
    id: str
    agencyName: str
    contactPerson: str
    contactPhone: str
    province: str
    city: str
    district: str
    address: str
    status: int
    auditRemark: Optional[str] = None
    createdAt: str
    updatedAt: str
