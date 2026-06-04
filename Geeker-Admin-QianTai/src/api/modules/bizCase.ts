import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";
import { ResPage } from "@/api/interface";

export interface CaseRecordRow {
  id: string;
  reportNumber: string;
  victimName: string;
  victimPhone: string;
  city: string;
  district: string;
  status: number;
  agencyId?: number | null;
  insuranceCompanyId?: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface CaseRecordListParams {
  pageNum: number;
  pageSize: number;
  reportNumber?: string;
  victimName?: string;
  status?: number;
}

export interface CaseRecordForm {
  reportNumber: string;
  victimName: string;
  victimPhone: string;
  city: string;
  district: string;
  status: number;
  agencyId?: number | null;
  insuranceCompanyId?: number | null;
}

export const getCaseRecordList = (params: CaseRecordListParams) => {
  return http.get<ResPage<CaseRecordRow>>(PORT1 + `/biz/case`, params);
};

export const getCaseRecordDetail = (id: string) => {
  return http.get<CaseRecordRow>(PORT1 + `/biz/case/${id}`);
};

export const addCaseRecord = (params: CaseRecordForm) => {
  return http.post(PORT1 + `/biz/case`, params);
};

export const editCaseRecord = (id: string, params: Partial<CaseRecordForm>) => {
  return http.put(PORT1 + `/biz/case/${id}`, params);
};

export const deleteCaseRecord = (id: string) => {
  return http.delete(PORT1 + `/biz/case/${id}`);
};
