<template>
  <div class="agency-onboard-audit-page">
    <AuditListPanel fixed-biz-type="agency_onboard" default-status="pending" :show-status-filter="true" />
    <el-card v-if="legacyTotal > 0" shadow="never" class="legacy-card">
      <template #header>
        <div class="legacy-card__head">
          <span>历史待审机构（无审核记录）</span>
          <el-tag type="warning" size="small">{{ legacyTotal }} 条</el-tag>
        </div>
      </template>
      <el-table v-loading="legacyLoading" :data="legacyRows" border stripe>
        <el-table-column prop="agencyName" label="机构名称" min-width="160" />
        <el-table-column prop="contactPerson" label="联系人" width="120" />
        <el-table-column prop="contactPhone" label="联系电话" width="140" />
        <el-table-column label="所在地区" min-width="180">
          <template #default="{ row }">{{ formatRegion(row.province, row.city, row.district) }}</template>
        </el-table-column>
        <el-table-column prop="createdAt" label="提交时间" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-auth="'agency:audit'" type="success" link @click="openAudit(row)">审核</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="auditDialogVisible" title="审核鉴定机构" width="520px" destroy-on-close @closed="resetAuditForm">
      <el-form ref="auditFormRef" :model="auditForm" :rules="auditRules" label-width="100px">
        <el-form-item label="机构名称">
          <span>{{ auditTargetName }}</span>
        </el-form-item>
        <el-form-item label="审核结果" prop="status">
          <el-radio-group v-model="auditForm.status">
            <el-radio v-for="item in AGENCY_AUDIT_RESULT_OPTIONS" :key="item.value" :value="item.value">
              {{ item.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="auditForm.status === 3" label="驳回原因" prop="auditRemark">
          <el-input
            v-model="auditForm.auditRemark"
            type="textarea"
            :rows="3"
            placeholder="请输入驳回原因"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="auditDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="auditSubmitLoading" @click="submitAudit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="agencyOnboardAudit">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, FormInstance } from "element-plus";
import type { FormRules } from "element-plus";
import AuditListPanel from "../components/AuditListPanel.vue";
import { auditAgency, getAgencyOnboardLegacyPending, type AgencyRow } from "@/api/modules/bizAgency";
import { AGENCY_AUDIT_RESULT_OPTIONS } from "@/constants/business";
import { formatRegionText } from "@/utils/region";

const legacyLoading = ref(false);
const legacyRows = ref<AgencyRow[]>([]);
const legacyTotal = ref(0);

const auditDialogVisible = ref(false);
const auditFormRef = ref<FormInstance>();
const auditSubmitLoading = ref(false);
const auditTargetId = ref("");
const auditTargetName = ref("");

const auditForm = reactive({
  status: 1 as 1 | 3,
  auditRemark: ""
});

const auditRules: FormRules = {
  status: [{ required: true, message: "请选择审核结果", trigger: "change" }],
  auditRemark: [
    {
      validator: (_rule, value, callback) => {
        if (auditForm.status === 3 && !String(value || "").trim()) {
          callback(new Error("驳回时请填写原因"));
          return;
        }
        callback();
      },
      trigger: "blur"
    }
  ]
};

const formatRegion = (province: string, city: string, district: string) => formatRegionText(province, city, district);

const fetchLegacy = async () => {
  legacyLoading.value = true;
  try {
    const res = await getAgencyOnboardLegacyPending({ pageNum: 1, pageSize: 50 });
    legacyRows.value = res.data?.list || [];
    legacyTotal.value = res.data?.total || 0;
  } finally {
    legacyLoading.value = false;
  }
};

const openAudit = (row: AgencyRow) => {
  auditTargetId.value = row.id;
  auditTargetName.value = row.agencyName;
  auditDialogVisible.value = true;
};

const resetAuditForm = () => {
  auditTargetId.value = "";
  auditTargetName.value = "";
  auditForm.status = 1;
  auditForm.auditRemark = "";
  auditFormRef.value?.resetFields();
};

const submitAudit = async () => {
  if (!auditFormRef.value || !auditTargetId.value) return;
  await auditFormRef.value.validate();
  auditSubmitLoading.value = true;
  try {
    await auditAgency(auditTargetId.value, {
      status: auditForm.status,
      auditRemark: auditForm.status === 3 ? auditForm.auditRemark : undefined
    });
    ElMessage.success(auditForm.status === 1 ? "审核通过" : "已驳回");
    auditDialogVisible.value = false;
    await fetchLegacy();
  } finally {
    auditSubmitLoading.value = false;
  }
};

onMounted(fetchLegacy);
</script>

<style scoped lang="scss">
.agency-onboard-audit-page {
  .legacy-card {
    margin-top: 16px;

    &__head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
  }
}
</style>
