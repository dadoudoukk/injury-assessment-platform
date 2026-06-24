<template>
  <el-drawer v-model="visible" :title="drawerTitle" size="min(760px, 96vw)" destroy-on-close @closed="onClosed">
    <div v-loading="loading" class="audit-detail-body">
      <template v-if="detail.id">
        <el-descriptions :column="2" border class="block">
          <el-descriptions-item label="审核 ID">{{ detail.id }}</el-descriptions-item>
          <el-descriptions-item label="业务类型">
            <el-tag :type="(bizTypeMeta?.tagType || 'info') as any">{{ bizTypeMeta?.label || detail.bizType }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="业务 ID">{{ detail.bizId }}</el-descriptions-item>
          <el-descriptions-item label="提交批次">第 {{ detail.submitBatch }} 次</el-descriptions-item>
          <el-descriptions-item label="审核状态">
            <el-tag :type="(statusMeta?.tagType || 'info') as any">{{ statusMeta?.label || detail.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ detail.createdAt || "—" }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.auditedAt" label="审核时间">{{ detail.auditedAt }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.auditRemark" label="驳回原因" :span="2">
            {{ detail.auditRemark }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="summaryItems.length" class="section-title">业务摘要</div>
        <el-descriptions v-if="summaryItems.length" :column="2" border class="block">
          <el-descriptions-item v-for="item in summaryItems" :key="item.label" :label="item.label" :span="item.span ?? 1">
            {{ item.value }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">本批次提交内容</div>
        <AuditPayloadBlock :biz-type="detail.bizType" :payload="detail.submitPayload" />

        <div class="section-title">批次历史</div>
        <p v-if="detail.bizType === 'agency_submit'" class="section-hint">每批次为完整文书包（文书编号 + 电子证书）提交</p>
        <el-timeline v-if="detail.batchHistory?.length">
          <el-timeline-item
            v-for="batch in detail.batchHistory"
            :key="batch.id"
            :timestamp="batch.createdAt"
            placement="top"
            :type="batchTimelineType(batch.status)"
          >
            <div class="batch-card">
              <div class="batch-card__head">
                <span>第 {{ batch.submitBatch }} 次提交</span>
                <el-tag size="small" :type="(auditStatusMap[batch.status]?.tagType || 'info') as any">
                  {{ auditStatusMap[batch.status]?.label || batch.status }}
                </el-tag>
              </div>
              <div v-if="batch.auditRemark" class="batch-card__remark">驳回原因：{{ batch.auditRemark }}</div>
              <div v-if="batch.auditedAt" class="batch-card__meta">审核时间：{{ batch.auditedAt }}</div>
              <AuditPayloadBlock :biz-type="detail.bizType" :payload="batch.submitPayload" compact />
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无批次历史" />
      </template>
    </div>
    <template v-if="showActions" #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button v-if="canReject" type="danger" plain @click="emitReject">驳回</el-button>
      <el-button v-if="canApprove" type="primary" :loading="approveLoading" @click="submitApprove">通过</el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { approveAudit, getAuditDetail, type AuditDetail } from "@/api/modules/bizAudit";
import {
  AUDIT_APPROVE_PERM_BY_BIZ_TYPE,
  AUDIT_REJECT_PERM_BY_BIZ_TYPE,
  auditBizTypeMap,
  auditStatusMap,
  type AuditBizType,
  type AuditStatus
} from "@/constants/audit";
import { formatRegionText } from "@/utils/region";
import { useAuthButtons } from "@/hooks/useAuthButtons";
import AuditPayloadBlock from "./AuditPayloadBlock.vue";

interface DrawerParams {
  auditId: string;
  refresh?: () => void;
  onReject?: (auditId: string) => void;
}

const emit = defineEmits<{ reject: [auditId: string] }>();

const { BUTTONS } = useAuthButtons();

const visible = ref(false);
const loading = ref(false);
const approveLoading = ref(false);
const paramsRef = ref<DrawerParams | null>(null);
const detail = reactive<Partial<AuditDetail>>({});

const bizTypeMeta = computed(() => (detail.bizType ? auditBizTypeMap[detail.bizType] : undefined));
const statusMeta = computed(() => (detail.status ? auditStatusMap[detail.status] : undefined));

const drawerTitle = computed(() => {
  const label = bizTypeMeta.value?.label || "审核";
  return `${label}详情`;
});

const approvePerm = computed(() => (detail.bizType ? AUDIT_APPROVE_PERM_BY_BIZ_TYPE[detail.bizType as AuditBizType] : ""));
const rejectPerm = computed(() => (detail.bizType ? AUDIT_REJECT_PERM_BY_BIZ_TYPE[detail.bizType as AuditBizType] : ""));

const canApprove = computed(() => !!approvePerm.value && !!BUTTONS.value[approvePerm.value]);
const canReject = computed(() => !!rejectPerm.value && !!BUTTONS.value[rejectPerm.value]);

const showActions = computed(() => detail.status === "pending" && !!detail.id && (canApprove.value || canReject.value));

const summaryItems = computed(() => {
  const s = detail.summary;
  if (!s) return [] as { label: string; value: string; span?: number }[];
  const items: { label: string; value: string; span?: number }[] = [];
  const push = (label: string, value?: string | number | null, span?: number) => {
    if (value != null && String(value).trim()) items.push({ label, value: String(value), span });
  };
  push("出险报案号", s.reportNumber);
  push("伤者姓名", s.victimName);
  push("联系电话", s.victimPhone);
  push("报案日期", s.reportDate);
  const region = formatRegionText(s.province, s.city, s.district);
  push("报案地区", region, 2);
  push("事故类型", s.accidentType);
  push("伤情类型", s.injuryType);
  push("保险公司", s.insuranceCompany);
  push("机构名称", s.agencyName);
  push("联系人", s.contactPerson);
  push("联系电话", s.contactPhone);
  push("详细地址", s.address, 2);
  return items;
});

const batchTimelineType = (status: AuditStatus) => {
  if (status === "approved") return "success";
  if (status === "rejected") return "danger";
  return "primary";
};

const resetDetail = () => {
  Object.keys(detail).forEach(key => {
    delete (detail as Record<string, unknown>)[key];
  });
};

const loadDetail = async (auditId: string) => {
  loading.value = true;
  try {
    const res = await getAuditDetail(auditId);
    Object.assign(detail, res.data);
  } catch {
    visible.value = false;
  } finally {
    loading.value = false;
  }
};

const acceptParams = async (params: DrawerParams) => {
  paramsRef.value = params;
  resetDetail();
  visible.value = true;
  await loadDetail(params.auditId);
};

const onClosed = () => {
  resetDetail();
  paramsRef.value = null;
};

const emitReject = () => {
  if (!detail.id) return;
  if (paramsRef.value?.onReject) {
    paramsRef.value.onReject(detail.id);
  } else {
    emit("reject", detail.id);
  }
};

const submitApprove = async () => {
  if (!detail.id) return;
  approveLoading.value = true;
  try {
    await approveAudit(detail.id);
    ElMessage.success("审核通过");
    visible.value = false;
    paramsRef.value?.refresh?.();
  } finally {
    approveLoading.value = false;
  }
};

defineExpose({ acceptParams });
</script>

<style scoped lang="scss">
.audit-detail-body {
  min-height: 120px;
}
.block {
  margin-bottom: 16px;
}
.section-title {
  margin: 16px 0 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.section-hint {
  margin: -4px 0 10px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.batch-card {
  padding: 8px 0 4px;
  &__head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    font-weight: 500;
  }
  &__remark {
    margin-bottom: 4px;
    color: var(--el-color-danger);
    font-size: 13px;
  }
  &__meta {
    margin-bottom: 8px;
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
}
</style>
