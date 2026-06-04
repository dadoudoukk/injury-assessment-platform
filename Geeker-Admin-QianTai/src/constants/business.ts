import type { EnumProps } from "@/components/ProTable/interface";

/** 鉴定机构状态：0待审核 1正常 2已停用 3审核驳回 */
export const AGENCY_STATUS_OPTIONS: EnumProps[] = [
  { label: "待审核", value: 0, tagType: "warning" },
  { label: "正常", value: 1, tagType: "success" },
  { label: "已停用", value: 2, tagType: "info" },
  { label: "审核驳回", value: 3, tagType: "danger" }
];

export type AgencyStatusMeta = { label: string; tagType: string };

/** 由 options 派生，供表格 el-tag 渲染使用 */
export const agencyStatusMap: Record<number, AgencyStatusMeta> = AGENCY_STATUS_OPTIONS.reduce(
  (acc, item) => {
    if (item.value !== undefined && item.value !== null) {
      acc[Number(item.value)] = {
        label: String(item.label ?? ""),
        tagType: String(item.tagType ?? "info")
      };
    }
    return acc;
  },
  {} as Record<number, AgencyStatusMeta>
);

export const getAgencyStatusMeta = (status: number): AgencyStatusMeta | undefined => {
  return agencyStatusMap[status];
};

/** 审核弹窗：通过 / 驳回 */
export const AGENCY_AUDIT_RESULT_OPTIONS = [
  { label: "通过", value: 1 },
  { label: "驳回", value: 3 }
] as const;
