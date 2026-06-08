import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";
import { ResPage } from "@/api/interface";

/** 报告附件项（与后端 ReportFileItem 一致） */
export interface ReportFileItem {
  url: string;
  name?: string;
  mime?: string;
}

export interface CaseRecordRow {
  id: string;
  reportNumber: string;
  victimName: string;
  victimPhone: string;
  reportDate: string;
  province: string;
  city: string;
  district: string;
  accidentType: string;
  injuryType: string;
  insuranceCompany: string;
  status: number;
  agencyId?: number | null;
  agencyName?: string | null;
  appraisalAmount?: string | null;
  appraisalConclusion?: string | null;
  reportFiles?: ReportFileItem[] | null;
  appraisalSubmittedAt?: string | null;
  appraisalSubmittedBy?: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface CaseRecordListParams {
  pageNum: number;
  pageSize: number;
  reportNumber?: string;
  victimName?: string;
  status?: number;
  insuranceCompany?: string;
  agencyId?: number;
  reportDateStart?: string;
  reportDateEnd?: string;
}

export interface CaseRecordForm {
  reportNumber: string;
  victimName: string;
  victimPhone: string;
  reportDate: string;
  province: string;
  city: string;
  district: string;
  accidentType: string;
  injuryType: string;
  insuranceCompany: string;
  status: number;
  agencyId?: number | null;
}

export interface CaseAppraisalSubmit {
  appraisalAmount: string | number;
  appraisalConclusion: string;
  reportFiles: ReportFileItem[];
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

export const submitCaseAppraisal = (id: string, params: CaseAppraisalSubmit) => {
  return http.post(PORT1 + `/biz/case/${id}/appraisal`, params);
};
