from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, make_response, require_permission, require_user
from models import BizInsuranceCompany
from schemas.business import (
    BizInsuranceCompanyCreate,
    BizInsuranceCompanyListQuery,
    BizInsuranceCompanyOut,
    BizInsuranceCompanyUpdate,
)

router = APIRouter(prefix="/biz/insurance", tags=["业务-保险公司管理"])


def _insurance_row(row: BizInsuranceCompany) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "companyName": row.company_name,
        "contactPerson": row.contact_person,
        "contactPhone": row.contact_phone,
        "status": row.status,
        "remark": row.remark,
        "createdAt": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else "",
        "updatedAt": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else "",
    }


@router.get("", dependencies=[Depends(require_permission("insurance:query"))])
async def insurance_list(
    query: BizInsuranceCompanyListQuery = Depends(),
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    stmt = select(BizInsuranceCompany).where(BizInsuranceCompany.is_delete == 0)
    
    if query.companyName:
        stmt = stmt.where(BizInsuranceCompany.company_name.like(f"%{query.companyName.strip()}%"))
    if query.status is not None:
        stmt = stmt.where(BizInsuranceCompany.status == query.status)

    count_stmt = select(func.count()).select_from(BizInsuranceCompany).where(*stmt._where_criteria)
    total = int((await db.scalar(count_stmt)) or 0)

    stmt = stmt.order_by(BizInsuranceCompany.id.desc())
    stmt = stmt.offset((query.pageNum - 1) * query.pageSize).limit(query.pageSize)
    
    rows = (await db.scalars(stmt)).all()
    
    return make_response(
        200,
        data={
            "list": [_insurance_row(r) for r in rows],
            "pageNum": query.pageNum,
            "pageSize": query.pageSize,
            "total": total,
        },
        msg="success"
    )

@router.get("/all")
async def insurance_all(
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    """获取所有正常的保险公司，用于下拉列表等"""
    stmt = select(BizInsuranceCompany).where(
        BizInsuranceCompany.is_delete == 0,
        BizInsuranceCompany.status == 1
    ).order_by(BizInsuranceCompany.id.desc())
    
    rows = (await db.scalars(stmt)).all()
    
    return make_response(
        200,
        data=[_insurance_row(r) for r in rows],
        msg="success"
    )

@router.post("", dependencies=[Depends(require_permission("insurance:add"))])
async def insurance_create(
    body: BizInsuranceCompanyCreate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    new_company = BizInsuranceCompany(
        company_name=body.companyName.strip(),
        contact_person=body.contactPerson.strip() if body.contactPerson else None,
        contact_phone=body.contactPhone.strip() if body.contactPhone else None,
        status=body.status,
        remark=body.remark.strip() if body.remark else None,
    )
    db.add(new_company)
    await db.commit()
    return make_response(200, data={}, msg="新增保险公司成功")


@router.put("/{company_id}", dependencies=[Depends(require_permission("insurance:edit"))])
async def insurance_update(
    company_id: int,
    body: BizInsuranceCompanyUpdate,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    company = await db.get(BizInsuranceCompany, company_id)
    if not company or company.is_delete == 1:
        return make_response(404, data={}, msg="保险公司不存在")

    if body.companyName is not None:
        company.company_name = body.companyName.strip()
    if body.contactPerson is not None:
        company.contact_person = body.contactPerson.strip() if body.contactPerson.strip() else None
    if body.contactPhone is not None:
        company.contact_phone = body.contactPhone.strip() if body.contactPhone.strip() else None
    if body.status is not None:
        company.status = body.status
    if body.remark is not None:
        company.remark = body.remark.strip() if body.remark.strip() else None

    await db.commit()
    return make_response(200, data={}, msg="更新保险公司成功")


@router.delete("/{company_id}", dependencies=[Depends(require_permission("insurance:delete"))])
async def insurance_delete(
    company_id: int,
    db: AsyncSession = Depends(get_async_db),
    x_access_token: Optional[str] = Header(default=None, alias="x-access-token"),
) -> Dict[str, Any]:
    company = await db.get(BizInsuranceCompany, company_id)
    if not company or company.is_delete == 1:
        return make_response(404, data={}, msg="保险公司不存在")

    company.is_delete = 1
    await db.commit()
    return make_response(200, data={}, msg="删除保险公司成功")