import type { EnumProps } from "@/components/ProTable/interface";

export type AuditBizType = "case_submit" | "agency_submit" | "agency_onboard";
export type AuditStatus = "pending" | "approved" | "rejected";

export const AUDIT_BIZ_TYPE_OPTIONS: EnumProps[] = [
  { label: "案件提交", value: "case_submit", tagType: "primary" },
  { label: "机构报告", value: "agency_submit", tagType: "warning" },
  { label: "机构入驻", value: "agency_onboard", tagType: "info" }
];

export const AUDIT_STATUS_OPTIONS: EnumProps[] = [
  { label: "待审核", value: "pending", tagType: "warning" },
  { label: "已通过", value: "approved", tagType: "success" },
  { label: "已驳回", value: "rejected", tagType: "danger" }
];

export const auditBizTypeMap = AUDIT_BIZ_TYPE_OPTIONS.reduce(
  (acc, item) => {
    if (item.value != null) {
      acc[String(item.value)] = {
        label: String(item.label ?? ""),
        tagType: String(item.tagType ?? "info")
      };
    }
    return acc;
  },
  {} as Record<string, { label: string; tagType: string }>
);

export const auditStatusMap = AUDIT_STATUS_OPTIONS.reduce(
  (acc, item) => {
    if (item.value != null) {
      acc[String(item.value)] = {
        label: String(item.label ?? ""),
        tagType: String(item.tagType ?? "info")
      };
    }
    return acc;
  },
  {} as Record<string, { label: string; tagType: string }>
);

export const AUDIT_QUERY_PERM_BY_BIZ_TYPE: Record<AuditBizType, string> = {
  case_submit: "case:platformAudit:query",
  agency_submit: "case:agencySubmitAudit:query",
  agency_onboard: "agency:query"
};

export const AUDIT_APPROVE_PERM_BY_BIZ_TYPE: Record<AuditBizType, string> = {
  case_submit: "case:platformAudit:approve",
  agency_submit: "case:agencySubmitAudit:approve",
  agency_onboard: "agency:audit"
};

export const AUDIT_REJECT_PERM_BY_BIZ_TYPE: Record<AuditBizType, string> = {
  case_submit: "case:platformAudit:reject",
  agency_submit: "case:agencySubmitAudit:reject",
  agency_onboard: "agency:audit"
};
