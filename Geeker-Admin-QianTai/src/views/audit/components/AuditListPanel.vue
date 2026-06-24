<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
      :init-param="tableInitParam"
    >
      <template #operation="scope">
        <el-button type="primary" link :icon="View" @click="openDetail(scope.row)">查看</el-button>
        <template v-if="scope.row.status === 'pending'">
          <el-button
            v-if="canApprove(scope.row.bizType)"
            type="success"
            link
            :icon="CircleCheck"
            @click="quickApprove(scope.row)"
          >
            通过
          </el-button>
          <el-button v-if="canReject(scope.row.bizType)" type="danger" link :icon="CircleClose" @click="openReject(scope.row)">
            驳回
          </el-button>
        </template>
      </template>
    </ProTable>

    <AuditDetailDrawer ref="detailDrawerRef" @reject="openRejectById" />
    <AuditRejectDialog ref="rejectDialogRef" />
  </div>
</template>

<script setup lang="tsx">
import { computed, ref } from "vue";
import { CircleCheck, CircleClose, View } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import ProTable from "@/components/ProTable/index.vue";
import { ColumnProps, ProTableInstance } from "@/components/ProTable/interface";
import { approveAudit, getAuditList, type AuditListParams, type AuditRecordRow } from "@/api/modules/bizAudit";
import {
  AUDIT_APPROVE_PERM_BY_BIZ_TYPE,
  AUDIT_REJECT_PERM_BY_BIZ_TYPE,
  AUDIT_BIZ_TYPE_OPTIONS,
  AUDIT_STATUS_OPTIONS,
  auditBizTypeMap,
  auditStatusMap,
  type AuditBizType,
  type AuditStatus
} from "@/constants/audit";
import { useAuthButtons } from "@/hooks/useAuthButtons";
import AuditDetailDrawer from "./AuditDetailDrawer.vue";
import AuditRejectDialog from "./AuditRejectDialog.vue";

const props = withDefaults(
  defineProps<{
    fixedBizType?: AuditBizType;
    defaultStatus?: AuditStatus;
    showBizTypeFilter?: boolean;
    showStatusFilter?: boolean;
  }>(),
  {
    showBizTypeFilter: false,
    showStatusFilter: true
  }
);

const { BUTTONS } = useAuthButtons();

const proTable = ref<ProTableInstance>();
const detailDrawerRef = ref<InstanceType<typeof AuditDetailDrawer> | null>(null);
const rejectDialogRef = ref<InstanceType<typeof AuditRejectDialog> | null>(null);

const tableInitParam = computed(() => {
  const param: Record<string, string> = {};
  if (props.fixedBizType) param.bizType = props.fixedBizType;
  if (props.defaultStatus) param.status = props.defaultStatus;
  return param;
});

const refreshTable = () => proTable.value?.getTableList();

const getTableList = (params: AuditListParams) => getAuditList(params);

const dataCallback = (data: { list: AuditRecordRow[]; total: number }) => ({
  list: data.list,
  total: data.total
});

const approvePermOf = (bizType: AuditBizType) => AUDIT_APPROVE_PERM_BY_BIZ_TYPE[bizType];
const rejectPermOf = (bizType: AuditBizType) => AUDIT_REJECT_PERM_BY_BIZ_TYPE[bizType];

const canApprove = (bizType: AuditBizType) => !!BUTTONS.value[approvePermOf(bizType)];
const canReject = (bizType: AuditBizType) => !!BUTTONS.value[rejectPermOf(bizType)];

const summaryLabel = (row: AuditRecordRow) => {
  const s = row.summary;
  if (!s) return "—";
  if (row.bizType === "agency_onboard") return s.agencyName || "—";
  if (row.bizType === "agency_submit") return s.reportNumber ? `${s.reportNumber} / ${s.victimName || ""}` : "—";
  return s.reportNumber ? `${s.reportNumber} / ${s.victimName || ""}` : "—";
};

const openDetail = (row: AuditRecordRow) => {
  detailDrawerRef.value?.acceptParams({
    auditId: row.id,
    refresh: refreshTable,
    onReject: openRejectById
  });
};

const openReject = (row: AuditRecordRow) => {
  rejectDialogRef.value?.acceptParams({ auditId: row.id, refresh: refreshTable });
};

const openRejectById = (auditId: string) => {
  rejectDialogRef.value?.acceptParams({ auditId, refresh: refreshTable });
};

const quickApprove = async (row: AuditRecordRow) => {
  await ElMessageBox.confirm("确认通过该审核记录？", "审核通过", {
    type: "warning",
    confirmButtonText: "通过",
    cancelButtonText: "取消"
  });
  await approveAudit(row.id);
  ElMessage.success("审核通过");
  refreshTable();
};

const columns = computed<ColumnProps<AuditRecordRow>[]>(() => {
  const cols: ColumnProps<AuditRecordRow>[] = [
    { type: "index", label: "#", width: 56 },
    {
      prop: "bizType",
      label: "业务类型",
      width: 120,
      search: props.showBizTypeFilter ? { el: "select", props: { placeholder: "业务类型", clearable: true } } : undefined,
      enum: AUDIT_BIZ_TYPE_OPTIONS,
      render: scope => {
        const item = auditBizTypeMap[scope.row.bizType];
        return <el-tag type={(item?.tagType || "info") as any}>{item?.label || scope.row.bizType}</el-tag>;
      }
    },
    {
      prop: "summary",
      label: "摘要",
      minWidth: 200,
      render: scope => summaryLabel(scope.row)
    },
    { prop: "submitBatch", label: "批次", width: 72, render: scope => `第 ${scope.row.submitBatch} 次` },
    {
      prop: "status",
      label: "审核状态",
      width: 100,
      search: props.showStatusFilter ? { el: "select", props: { placeholder: "审核状态", clearable: true } } : undefined,
      enum: AUDIT_STATUS_OPTIONS,
      render: scope => {
        const item = auditStatusMap[scope.row.status];
        return <el-tag type={(item?.tagType || "info") as any}>{item?.label || scope.row.status}</el-tag>;
      }
    },
    { prop: "createdAt", label: "提交时间", width: 170 },
    { prop: "auditedAt", label: "审核时间", width: 170 },
    { prop: "operation", label: "操作", fixed: "right", width: 220 }
  ];
  return cols;
});
</script>
