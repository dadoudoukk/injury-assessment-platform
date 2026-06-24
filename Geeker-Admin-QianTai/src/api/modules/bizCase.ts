import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";
import { ResPage } from "@/api/interface";

/** 报告附件项（历史只读） */
export interface ReportFileItem {
  url: string;
  name?: string;
  mime?: string;
}

/** 鉴定视频项 */
export interface AppraisalVideoItem {
  url: string;
  name?: string;
}

/** 电子证书项 */
export interface ElectronicCertificateItem {
  url: string;
  name?: string;
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
  /** 历史字段，有值时只读展示 */
  appraisalAmount?: string | null;
  appraisalConclusion?: string | null;
  reportFiles?: ReportFileItem[] | null;
  appraisalVideos?: AppraisalVideoItem[] | null;
  documentNumber?: string | null;
  electronicCertificate?: ElectronicCertificateItem | null;
  /** status=6 时 pending 审核记录 ID（列表/详情摘要） */
  pendingAgencySubmitAuditId?: string | null;
  /** 文书字段来源：main | pending_payload | hidden | legacy_main */
  documentFieldsSource?: string | null;
  appraisalSubmittedAt?: string | null;
  appraisalSubmittedBy?: number | null;
  reworkRemark?: string | null;
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

export const exportCaseRecord = (params: CaseRecordListParams) => {
  return http.download(PORT1 + `/biz/case/export`, params);
};

export const reworkCaseRecord = (id: string, params: { remark: string }) => {
  return http.post(PORT1 + `/biz/case/${id}/rework`, params);
};

export interface CaseTrendStat {
  date: string;
  fullDate: string;
  count: number;
}

export interface CaseStatusStat {
  name: string;
  value: number;
}

export interface CaseRecentActivity {
  content: string;
  timestamp: string;
  type?: "primary" | "success" | "warning" | "danger" | "info";
}

export interface CaseStatsData {
  total?: number;
  pending?: number;
  accepted?: number;
  inProgress?: number;
  reportPendingAudit?: number;
  completed?: number;
  rework?: number;
  agencyCount?: number;
  insuranceCount?: number;
  weekGrowth?: number;
  statusStats?: CaseStatusStat[];
  insuranceStats?: CaseStatusStat[];
  trendStats?: CaseTrendStat[];
  recentActivities?: CaseRecentActivity[];
}

export const getCaseStats = () => {
  return http.get<CaseStatsData>(PORT1 + `/biz/case/stats`, {}, { loading: false });
};

/** 案件状态常量 */
export const CASE_STATUS = {
  PENDING_CONFIRM: 1,
  ACCEPTED: 2,
  APPRAISING: 3,
  COMPLETED: 4,
  REWORK: 5,
  REPORT_PENDING_AUDIT: 6
} as const;

export const CASE_STATUS_OPTIONS = [
  { label: "待确认", value: CASE_STATUS.PENDING_CONFIRM },
  { label: "已受理", value: CASE_STATUS.ACCEPTED },
  { label: "鉴定中", value: CASE_STATUS.APPRAISING },
  { label: "已完成", value: CASE_STATUS.COMPLETED },
  { label: "已打回", value: CASE_STATUS.REWORK },
  { label: "报告待平台审核", value: CASE_STATUS.REPORT_PENDING_AUDIT }
];

export const CASE_STATUS_MAP: Record<number, { label: string; tagType: string }> = {
  [CASE_STATUS.PENDING_CONFIRM]: { label: "待确认", tagType: "warning" },
  [CASE_STATUS.ACCEPTED]: { label: "已受理", tagType: "" },
  [CASE_STATUS.APPRAISING]: { label: "鉴定中", tagType: "primary" },
  [CASE_STATUS.COMPLETED]: { label: "已完成", tagType: "success" },
  [CASE_STATUS.REWORK]: { label: "已打回", tagType: "danger" },
  [CASE_STATUS.REPORT_PENDING_AUDIT]: { label: "报告待平台审核", tagType: "warning" }
};
