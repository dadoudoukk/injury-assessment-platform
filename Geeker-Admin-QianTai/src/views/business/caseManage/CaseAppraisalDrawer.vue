<template>
  <el-drawer v-model="visible" :title="drawerTitle" size="min(720px, 96vw)" destroy-on-close @closed="onClosed">
    <div v-loading="loading" class="appraisal-drawer-body">
      <el-descriptions v-if="summary.reportNumber" :column="2" border class="case-summary">
        <el-descriptions-item label="出险报案号">{{ summary.reportNumber }}</el-descriptions-item>
        <el-descriptions-item label="伤者姓名">{{ summary.victimName }}</el-descriptions-item>
        <el-descriptions-item v-if="!isAgencyMode" label="鉴定机构" :span="2">{{ summary.agencyName }}</el-descriptions-item>
      </el-descriptions>

      <el-form
        ref="formRef"
        :model="form"
        :rules="isReadonly ? undefined : rules"
        :disabled="isReadonly"
        :hide-required-asterisk="isReadonly"
        label-width="110px"
        class="appraisal-form"
      >
        <el-form-item label="鉴定金额" prop="appraisalAmount">
          <el-input v-model="form.appraisalAmount" placeholder="请输入鉴定金额（元）" clearable maxlength="20">
            <template #append>元</template>
          </el-input>
        </el-form-item>
        <el-form-item label="鉴定结论" prop="appraisalConclusion">
          <el-input
            v-model="form.appraisalConclusion"
            type="textarea"
            :rows="4"
            placeholder="请输入鉴定结论"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="报告附件" prop="reportFiles">
          <UploadFiles v-model:files="form.reportFiles" :disabled="isReadonly" />
        </el-form-item>
      </el-form>
    </div>

    <template v-if="!isReadonly" #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts" name="CaseAppraisalDrawer">
import { computed, reactive, ref } from "vue";
import { ElMessage, FormInstance } from "element-plus";
import type { FormRules } from "element-plus";
import UploadFiles from "@/components/Upload/Files.vue";
import {
  getCaseRecordDetail,
  submitCaseAppraisal,
  type CaseAppraisalSubmit,
  type CaseRecordRow,
  type ReportFileItem
} from "@/api/modules/bizCase";
import { useTenantMode } from "@/hooks/useTenantMode";
import type { AppraisalDrawerMode } from "./useCaseActions";

const { isAgencyMode } = useTenantMode();

interface AppraisalDrawerParams {
  mode: AppraisalDrawerMode;
  caseId: string;
  refresh?: () => void;
}

interface AppraisalFormState {
  appraisalAmount: string;
  appraisalConclusion: string;
  reportFiles: ReportFileItem[];
}

const AMOUNT_RE = /^(?:0|[1-9]\d*)(?:\.\d{1,2})?$/;

const visible = ref(false);
const loading = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const drawerParams = ref<AppraisalDrawerParams | null>(null);

const summary = reactive({
  reportNumber: "",
  victimName: "",
  agencyName: ""
});

const form = reactive<AppraisalFormState>({
  appraisalAmount: "",
  appraisalConclusion: "",
  reportFiles: []
});

const isReadonly = computed(() => drawerParams.value?.mode === "view");

const drawerTitle = computed(() => {
  const map: Record<AppraisalDrawerMode, string> = {
    submit: "出具鉴定报告",
    edit: "修改鉴定报告",
    view: "查看鉴定报告"
  };
  return map[drawerParams.value?.mode ?? "submit"];
});

const validateAmount = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  const text = (value || "").trim();
  if (!text) {
    callback(new Error("请输入鉴定金额"));
    return;
  }
  if (!AMOUNT_RE.test(text) || Number(text) <= 0) {
    callback(new Error("请输入大于 0 的金额，最多两位小数"));
    return;
  }
  callback();
};

const validateReportFiles = (_rule: unknown, value: ReportFileItem[], callback: (error?: Error) => void) => {
  if (!value?.length) {
    callback(new Error("请至少上传一份报告附件"));
    return;
  }
  callback();
};

const rules: FormRules = {
  appraisalAmount: [{ required: true, validator: validateAmount, trigger: "blur" }],
  appraisalConclusion: [{ required: true, message: "请输入鉴定结论", trigger: "blur" }],
  reportFiles: [{ required: true, validator: validateReportFiles, trigger: "change" }]
};

const resetSummary = () => {
  summary.reportNumber = "";
  summary.victimName = "";
  summary.agencyName = "";
};

const resetForm = () => {
  form.appraisalAmount = "";
  form.appraisalConclusion = "";
  form.reportFiles = [];
  formRef.value?.clearValidate();
};

const mapDetailToAppraisalForm = (detail: CaseRecordRow): AppraisalFormState => ({
  appraisalAmount: detail.appraisalAmount ?? "",
  appraisalConclusion: detail.appraisalConclusion ?? "",
  reportFiles: Array.isArray(detail.reportFiles) ? [...detail.reportFiles] : []
});

const fillSummaryFromDetail = (detail: CaseRecordRow) => {
  summary.reportNumber = detail.reportNumber || "--";
  summary.victimName = detail.victimName || "--";
  summary.agencyName = detail.agencyName || "暂未指派";
};

const buildAppraisalPayload = (): CaseAppraisalSubmit => ({
  appraisalAmount: form.appraisalAmount.trim(),
  appraisalConclusion: form.appraisalConclusion.trim(),
  reportFiles: form.reportFiles
});

const loadDetail = async (caseId: string) => {
  loading.value = true;
  try {
    const res = await getCaseRecordDetail(caseId);
    fillSummaryFromDetail(res.data);
    Object.assign(form, mapDetailToAppraisalForm(res.data));
  } catch {
    visible.value = false;
  } finally {
    loading.value = false;
  }
};

const acceptParams = async (params: AppraisalDrawerParams) => {
  drawerParams.value = params;
  resetSummary();
  resetForm();
  visible.value = true;
  await loadDetail(params.caseId);
};

const handleSubmit = () => {
  if (drawerParams.value?.mode === "view") return;
  formRef.value?.validate(async valid => {
    if (!valid || !drawerParams.value) return;
    submitLoading.value = true;
    try {
      const res = await submitCaseAppraisal(drawerParams.value.caseId, buildAppraisalPayload());
      ElMessage.success({ message: res.msg || "提交成功" });
      visible.value = false;
      drawerParams.value.refresh?.();
    } catch {
      /* 全局拦截器已提示错误 */
    } finally {
      submitLoading.value = false;
    }
  });
};

const onClosed = () => {
  drawerParams.value = null;
  resetSummary();
  resetForm();
};

defineExpose({ acceptParams });
</script>

<style scoped lang="scss">
.appraisal-drawer-body {
  min-height: 200px;
}
.case-summary {
  margin-bottom: 20px;
}
.appraisal-form {
  margin-top: 4px;
}
</style>
