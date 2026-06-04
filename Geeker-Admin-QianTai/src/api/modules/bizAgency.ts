import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";
import { ResPage } from "@/api/interface";

export interface AgencyRow {
  id: string;
  agencyName: string;
  contactPerson: string;
  contactPhone: string;
  province: string;
  city: string;
  district: string;
  address: string;
  status: number;
  auditRemark?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AgencyListParams {
  pageNum: number;
  pageSize: number;
  agencyName?: string;
  contactPerson?: string;
  status?: number;
  province?: string;
  city?: string;
  district?: string;
}

export interface AgencyForm {
  agencyName: string;
  contactPerson: string;
  contactPhone: string;
  province: string;
  city: string;
  district: string;
  address: string;
}

export interface AgencyAuditForm {
  status: 1 | 3;
  auditRemark?: string;
}

export interface AgencyOption {
  id: string;
  agencyName: string;
}

export const getAgencyList = (params: AgencyListParams) => {
  return http.get<ResPage<AgencyRow>>(PORT1 + `/biz/agency`, params);
};

export const getAgencyDetail = (id: string) => {
  return http.get<AgencyRow>(PORT1 + `/biz/agency/${id}`);
};

export const addAgency = (params: AgencyForm) => {
  return http.post(PORT1 + `/biz/agency`, params);
};

export const editAgency = (id: string, params: Partial<AgencyForm>) => {
  return http.put(PORT1 + `/biz/agency/${id}`, params);
};

export const auditAgency = (id: string, params: AgencyAuditForm) => {
  return http.put(PORT1 + `/biz/agency/${id}/audit`, params);
};

export const deleteAgency = (id: string) => {
  return http.delete(PORT1 + `/biz/agency/${id}`);
};

export const getAgencyOptions = () => {
  return http.get<{ list: AgencyOption[] }>(PORT1 + `/biz/agency/options`);
};
