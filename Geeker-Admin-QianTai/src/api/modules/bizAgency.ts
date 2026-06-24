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
  excludeStatus?: number;
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

export interface AgencyRejectLogRow {
  id: string;
  caseId: string;
  reportNumber: string;
  victimName: string;
  rejectedAgencyId: number;
  rejectedAgencyName: string;
  currentAgencyId?: number | null;
  currentAgencyName?: string | null;
  caseStatus: number;
  caseStatusLabel: string;
  recordTime: string;
}

export interface AgencyRejectLogParams {
  pageNum: number;
  pageSize: number;
  agencyId?: number;
  reportNumber?: string;
}

export const getAgencyRejectLogList = (params: AgencyRejectLogParams) => {
  return http.get<ResPage<AgencyRejectLogRow>>(PORT1 + `/biz/agency/reject-log`, params);
};

export interface AgencyServiceScopeRow {
  id: string;
  agencyId: number;
  agencyName: string;
  province: string;
  city: string;
  district: string;
  regionText: string;
  createdAt: string;
}

export interface AgencyServiceScopeParams {
  pageNum: number;
  pageSize: number;
  agencyId?: number;
}

export interface AgencyServiceScopeForm {
  agencyId: number;
  province: string;
  city: string;
  district: string;
}

export const getAgencyServiceScopeList = (params: AgencyServiceScopeParams) => {
  return http.get<ResPage<AgencyServiceScopeRow>>(PORT1 + `/biz/agency/scope`, params);
};

export const addAgencyServiceScope = (params: AgencyServiceScopeForm) => {
  return http.post(PORT1 + `/biz/agency/scope`, params);
};

export const deleteAgencyServiceScope = (id: string) => {
  return http.delete(PORT1 + `/biz/agency/scope/${id}`);
};

export const getAgencyOnboardLegacyPending = (params: { pageNum: number; pageSize: number }) => {
  return http.get<ResPage<AgencyRow>>(PORT1 + `/biz/agency/onboard-legacy-pending`, params);
};
