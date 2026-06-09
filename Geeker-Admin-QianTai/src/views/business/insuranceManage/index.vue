<template>
  <div class="table-box">
    <ProTable ref="proTable" :columns="columns" :request-api="getTableList" :data-callback="dataCallback">
      <template #tableHeader>
        <el-button v-auth="'insurance:add'" type="primary" :icon="CirclePlus" @click="openAdd">新增保险公司</el-button>
      </template>
      <template #operation="scope">
        <el-button v-auth="'insurance:edit'" type="primary" link :icon="EditPen" @click="openEdit(scope.row)">编辑</el-button>
        <el-button v-auth="'insurance:delete'" type="danger" link :icon="Delete" @click="deleteOne(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑保险公司' : '新增保险公司'"
      width="640px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" v-loading="formLoading" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="公司名称" prop="companyName">
          <el-input v-model="form.companyName" placeholder="请输入保险公司名称" clearable maxlength="100" />
        </el-form-item>
        <el-form-item label="联系人" prop="contactPerson">
          <el-input v-model="form.contactPerson" placeholder="请输入联系人" clearable maxlength="50" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contactPhone">
          <el-input v-model="form.contactPhone" placeholder="请输入联系电话" clearable maxlength="20" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="tsx" name="insuranceManage">
import { reactive, ref } from "vue";
import { CirclePlus, Delete, EditPen } from "@element-plus/icons-vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import ProTable from "@/components/ProTable/index.vue";
import { ColumnProps, ProTableInstance } from "@/components/ProTable/interface";
import { useHandleData } from "@/hooks/useHandleData";
import {
  addInsurance,
  deleteInsurance,
  editInsurance,
  getInsuranceList,
  type InsuranceCompanyForm,
  type InsuranceCompanyRow
} from "@/api/modules/bizInsurance";

const proTable = ref<ProTableInstance>();
const dialogVisible = ref(false);
const formLoading = ref(false);
const submitLoading = ref(false);
const isEdit = ref(false);
const editId = ref("");
const formRef = ref<FormInstance>();

const form = reactive<InsuranceCompanyForm>({
  companyName: "",
  contactPerson: "",
  contactPhone: "",
  status: 1,
  remark: ""
});

const rules = reactive<FormRules>({
  companyName: [{ required: true, message: "请输入保险公司名称", trigger: "blur" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }]
});

const statusOptions = [
  { label: "正常", value: 1, tagType: "success" },
  { label: "停用", value: 0, tagType: "info" }
];

const columns: ColumnProps<InsuranceCompanyRow>[] = [
  { prop: "companyName", label: "公司名称", search: { el: "input" }, width: 220 },
  { prop: "contactPerson", label: "联系人", width: 120 },
  { prop: "contactPhone", label: "联系电话", width: 150 },
  {
    prop: "status",
    label: "状态",
    width: 100,
    search: {
      el: "select",
      props: {
        filterable: true
      }
    },
    enum: statusOptions,
    fieldNames: { label: "label", value: "value" },
    render: scope => {
      const option = statusOptions.find(item => item.value === scope.row.status);
      if (!option) return <span>--</span>;
      return <el-tag type={option.tagType as any}>{option.label}</el-tag>;
    }
  },
  { prop: "remark", label: "备注", minWidth: 200, showOverflowTooltip: true },
  { prop: "createdAt", label: "创建时间", width: 180 },
  { prop: "operation", label: "操作", fixed: "right", width: 150 }
];

const dataCallback = (data: any) => ({
  list: data.list,
  total: data.total
});

const getTableList = (params: any) => {
  return getInsuranceList(params);
};

const openAdd = () => {
  isEdit.value = false;
  editId.value = "";
  dialogVisible.value = true;
};

const openEdit = (row: InsuranceCompanyRow) => {
  isEdit.value = true;
  editId.value = row.id;
  form.companyName = row.companyName;
  form.contactPerson = row.contactPerson || "";
  form.contactPhone = row.contactPhone || "";
  form.status = row.status;
  form.remark = row.remark || "";
  dialogVisible.value = true;
};

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  form.companyName = "";
  form.contactPerson = "";
  form.contactPhone = "";
  form.status = 1;
  form.remark = "";
};

const submitForm = async () => {
  if (!formRef.value) return;
  await formRef.value.validate();

  submitLoading.value = true;
  try {
    if (isEdit.value) {
      await editInsurance(editId.value, form);
      ElMessage.success("修改成功");
    } else {
      await addInsurance(form);
      ElMessage.success("新增成功");
    }
    dialogVisible.value = false;
    proTable.value?.getTableList();
  } finally {
    submitLoading.value = false;
  }
};

const deleteOne = async (row: InsuranceCompanyRow) => {
  await useHandleData(deleteInsurance, row.id, `删除 ${row.companyName}`);
  proTable.value?.getTableList();
};
</script>

<style scoped lang="scss">
.table-box {
  height: 100%;
}
</style>