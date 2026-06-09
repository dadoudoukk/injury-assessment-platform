import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";
import { ResPage } from "@/api/interface";

export interface InsuranceCompanyRow {
  id: string;
  companyName: string;
  contactPerson?: string;
  contactPhone?: string;
  status: number;
  remark?: string;
  createdAt: string;
  updatedAt: string;
}

export interface InsuranceCompanyListParams {
  pageNum: number;
  pageSize: number;
  companyName?: string;
  status?: number;
}

export interface InsuranceCompanyForm {
  companyName: string;
  contactPerson?: string;
  contactPhone?: string;
  status: number;
  remark?: string;
}

export const getInsuranceList = (params: InsuranceCompanyListParams) => {
  return http.get<ResPage<InsuranceCompanyRow>>(PORT1 + `/biz/insurance`, params);
};

export const getInsuranceAll = () => {
  return http.get<InsuranceCompanyRow[]>(PORT1 + `/biz/insurance/all`);
};

export const addInsurance = (params: InsuranceCompanyForm) => {
  return http.post(PORT1 + `/biz/insurance`, params);
};

export const editInsurance = (id: string, params: Partial<InsuranceCompanyForm>) => {
  return http.put(PORT1 + `/biz/insurance/${id}`, params);
};

export const deleteInsurance = (id: string) => {
  return http.delete(PORT1 + `/biz/insurance/${id}`);
};
