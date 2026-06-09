import type { Component } from "vue";
import { computed } from "vue";
import { Delete, Document, EditPen, View } from "@element-plus/icons-vue";
import type { CaseRecordRow } from "@/api/modules/bizCase";
import { useAuthButtons } from "@/hooks/useAuthButtons";
import { useTenantMode } from "@/hooks/useTenantMode";

export type AppraisalDrawerMode = "submit" | "edit" | "view";

export interface CaseActionContext {
  openEdit: (row: CaseRecordRow) => void;
  openViewDetail: (row: CaseRecordRow) => void;
  openAppraisalDrawer: (row: CaseRecordRow, mode: AppraisalDrawerMode) => void;
  deleteOne: (row: CaseRecordRow) => void;
  openRework: (row: CaseRecordRow) => void;
}

export interface CaseRowAction {
  key: string;
  label: string;
  icon?: Component;
  type?: "primary" | "danger" | "success" | "warning";
  onClick: (row: CaseRecordRow) => void;
}

interface ActionDef {
  key: string;
  label: string;
  icon?: Component;
  type?: CaseRowAction["type"];
  auth?: string;
  /** 平台专属动作，机构模式下不可见 */
  platformOnly?: boolean;
  visible: (row: CaseRecordRow) => boolean;
  onClick: (ctx: CaseActionContext) => (row: CaseRecordRow) => void;
}

const STATUS_PENDING = 1;
const STATUS_IN_PROGRESS = 2;
const STATUS_COMPLETED = 3;

const ACTION_DEFS: ActionDef[] = [
  {
    key: "edit",
    label: "编辑",
    icon: EditPen,
    type: "primary",
    auth: "case:edit",
    platformOnly: true,
    visible: row => row.status === STATUS_PENDING || row.status === STATUS_IN_PROGRESS,
    onClick: ctx => ctx.openEdit
  },
  {
    key: "submitAppraisal",
    label: "出具报告",
    icon: Document,
    type: "primary",
    auth: "case:appraisal",
    visible: row => row.status === STATUS_IN_PROGRESS,
    onClick: ctx => row => ctx.openAppraisalDrawer(row, "submit")
  },
  {
    key: "viewDetail",
    label: "查看详情",
    icon: View,
    type: "primary",
    visible: row => row.status === STATUS_COMPLETED,
    onClick: ctx => ctx.openViewDetail
  },
  {
    key: "viewAppraisal",
    label: "查看报告",
    icon: View,
    type: "primary",
    auth: "case:appraisal",
    visible: row => row.status === STATUS_COMPLETED,
    onClick: ctx => row => ctx.openAppraisalDrawer(row, "view")
  },
  {
    key: "editAppraisal",
    label: "修改报告",
    icon: EditPen,
    type: "primary",
    auth: "case:appraisal",
    visible: row => row.status === STATUS_COMPLETED,
    onClick: ctx => row => ctx.openAppraisalDrawer(row, "edit")
  },
  {
    key: "rework",
    label: "复议打回",
    icon: Delete,
    type: "danger",
    auth: "case:edit",
    platformOnly: true,
    visible: row => row.status === STATUS_COMPLETED,
    onClick: ctx => ctx.openRework
  },
  {
    key: "delete",
    label: "删除",
    icon: Delete,
    type: "danger",
    auth: "case:delete",
    platformOnly: true,
    visible: row => row.status === STATUS_PENDING || row.status === STATUS_IN_PROGRESS || row.status === 4,
    onClick: ctx => ctx.deleteOne
  }
];

const hasAuth = (buttons: Record<string, boolean>, auth?: string) => {
  if (!auth) return true;
  return !!buttons[auth];
};

export function useCaseActions(ctx: CaseActionContext) {
  const { BUTTONS } = useAuthButtons();
  const { isAgencyMode } = useTenantMode();

  const canAddCase = computed(() => !isAgencyMode.value && hasAuth(BUTTONS.value, "case:add"));

  const getCaseRowActions = (row: CaseRecordRow): CaseRowAction[] => {
    return ACTION_DEFS.filter(def => {
      if (isAgencyMode.value && def.platformOnly) return false;
      if (!hasAuth(BUTTONS.value, def.auth)) return false;
      return def.visible(row);
    }).map(def => ({
      key: def.key,
      label: def.label,
      icon: def.icon,
      type: def.type,
      onClick: def.onClick(ctx)
    }));
  };

  return { getCaseRowActions, canAddCase, isAgencyMode };
}
