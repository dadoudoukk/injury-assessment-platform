import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";
import { ResPage } from "@/api/interface";
import type { AuditBizType, AuditStatus } from "@/constants/audit";

export interface AuditAttachmentItem {
  url: string;
  name?: string;
  mime?: string;
  category?: string;
  kind?: string;
}

export interface AuditSummary {
  reportNumber?: string;
  victimName?: string;
  victimPhone?: string;
  reportDate?: string;
  province?: string;
  city?: string;
  district?: string;
  accidentType?: string;
  injuryType?: string;
  insuranceCompany?: string;
  appStatus?: string;
  caseId?: string | null;
  status?: number;
  agencyId?: number | null;
  agencyName?: string;
  contactPerson?: string;
  contactPhone?: string;
  address?: string;
  agencyStatus?: number;
}

export interface AuditRecordRow {
  id: string;
  bizType: AuditBizType;
  bizId: string;
  submitBatch: number;
  status: AuditStatus;
  submitPayload?: Record<string, unknown> | null;
  auditRemark?: string;
  auditedBy?: number | null;
  auditedAt?: string;
  createdBy?: number | null;
  createdAt: string;
  updatedAt: string;
  summary?: AuditSummary | null;
}

export interface AuditBatchHistoryItem {
  id: string;
  submitBatch: number;
  status: AuditStatus;
  submitPayload?: Record<string, unknown> | null;
  auditRemark?: string;
  auditedBy?: number | null;
  auditedAt?: string;
  createdAt: string;
}

export interface AuditDetail extends AuditRecordRow {
  batchHistory: AuditBatchHistoryItem[];
}

export interface AuditListParams {
  pageNum: number;
  pageSize: number;
  bizType?: AuditBizType;
  status?: AuditStatus;
}

export const getAuditList = (params: AuditListParams) => {
  return http.get<ResPage<AuditRecordRow>>(PORT1 + `/biz/audit`, params);
};

export const getAuditDetail = (id: string) => {
  return http.get<AuditDetail>(PORT1 + `/biz/audit/${id}`);
};

export const approveAudit = (id: string) => {
  return http.put(PORT1 + `/biz/audit/${id}/approve`);
};

export const rejectAudit = (id: string, params: { auditRemark: string }) => {
  return http.put(PORT1 + `/biz/audit/${id}/reject`, params);
};
