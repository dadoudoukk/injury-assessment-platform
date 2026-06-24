<template>
  <el-dialog v-model="visible" title="审核驳回" width="520px" destroy-on-close @closed="onClosed">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="驳回原因" prop="auditRemark">
        <el-input
          v-model="form.auditRemark"
          type="textarea"
          :rows="4"
          placeholder="请输入驳回原因"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submit">确定驳回</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts" name="AuditRejectDialog">
import { reactive, ref } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { rejectAudit } from "@/api/modules/bizAudit";

interface RejectParams {
  auditId: string;
  refresh?: () => void;
}

const visible = ref(false);
const loading = ref(false);
const formRef = ref<FormInstance>();
const paramsRef = ref<RejectParams | null>(null);

const form = reactive({ auditRemark: "" });

const rules: FormRules = {
  auditRemark: [{ required: true, message: "请输入驳回原因", trigger: "blur" }]
};

const acceptParams = (params: RejectParams) => {
  paramsRef.value = params;
  form.auditRemark = "";
  visible.value = true;
};

const onClosed = () => {
  form.auditRemark = "";
  paramsRef.value = null;
};

const submit = async () => {
  if (!paramsRef.value) return;
  await formRef.value?.validate();
  loading.value = true;
  try {
    await rejectAudit(paramsRef.value.auditId, { auditRemark: form.auditRemark.trim() });
    ElMessage.success("已驳回");
    visible.value = false;
    paramsRef.value.refresh?.();
  } finally {
    loading.value = false;
  }
};

defineExpose({ acceptParams });
</script>
