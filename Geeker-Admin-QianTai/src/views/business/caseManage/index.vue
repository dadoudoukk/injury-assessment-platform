<template>
  <div class="table-box">
    <ProTable ref="proTable" :columns="columns" :request-api="getTableList" :data-callback="dataCallback">
      <template #tableHeader>
        <el-button v-auth="'case:add'" type="primary" :icon="CirclePlus" @click="openAdd">新增案件</el-button>
      </template>
      <template #operation="scope">
        <el-button v-auth="'case:edit'" type="primary" link :icon="EditPen" @click="openEdit(scope.row)">编辑</el-button>
        <el-button v-auth="'case:delete'" type="danger" link :icon="Delete" @click="deleteOne(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑案件' : '新增案件'"
      width="560px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="出险报案号" prop="reportNumber">
          <el-input v-model="form.reportNumber" placeholder="请输入出险报案号" clearable maxlength="50" />
        </el-form-item>
        <el-form-item label="伤者姓名" prop="victimName">
          <el-input v-model="form.victimName" placeholder="请输入伤者姓名" clearable maxlength="50" />
        </el-form-item>
        <el-form-item label="联系电话" prop="victimPhone">
          <el-input v-model="form.victimPhone" placeholder="请输入联系电话" clearable maxlength="20" />
        </el-form-item>
        <el-form-item label="报案城市" prop="city">
          <el-input v-model="form.city" placeholder="请输入报案城市" clearable maxlength="50" />
        </el-form-item>
        <el-form-item label="报案区县" prop="district">
          <el-input v-model="form.district" placeholder="请输入报案区县" clearable maxlength="50" />
        </el-form-item>
        <el-form-item label="案件状态" prop="status">
          <el-select v-model="form.status" placeholder="请选择案件状态" style="width: 100%">
            <el-option v-for="item in caseStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="tsx" name="caseManage">
import { reactive, ref } from "vue";
import { CirclePlus, Delete, EditPen } from "@element-plus/icons-vue";
import { ElMessage, FormInstance } from "element-plus";
import type { FormRules } from "element-plus";
import ProTable from "@/components/ProTable/index.vue";
import { ColumnProps, ProTableInstance } from "@/components/ProTable/interface";
import { addCaseRecord, deleteCaseRecord, editCaseRecord, getCaseRecordList, type CaseRecordRow } from "@/api/modules/bizCase";
import { useHandleData } from "@/hooks/useHandleData";

const caseStatusOptions = [
  { label: "待接单", value: 1, tagType: "warning" },
  { label: "鉴定中", value: 2, tagType: "primary" },
  { label: "已完成", value: 3, tagType: "success" }
];

const caseStatusMap: Record<number, { label: string; tagType: string }> = {
  1: { label: "待接单", tagType: "warning" },
  2: { label: "鉴定中", tagType: "primary" },
  3: { label: "已完成", tagType: "success" }
};

const proTable = ref<ProTableInstance>();
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();

const form = reactive({
  id: "",
  reportNumber: "",
  victimName: "",
  victimPhone: "",
  city: "",
  district: "",
  status: 1
});

const validatePhone = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (!value || !value.trim()) {
    callback(new Error("请输入联系电话"));
    return;
  }
  if (!/^1[3-9]\d{9}$/.test(value.trim())) {
    callback(new Error("请输入正确的手机号"));
    return;
  }
  callback();
};

const rules: FormRules = {
  reportNumber: [{ required: true, message: "请输入出险报案号", trigger: "blur" }],
  victimName: [{ required: true, message: "请输入伤者姓名", trigger: "blur" }],
  victimPhone: [{ required: true, validator: validatePhone, trigger: "blur" }],
  city: [{ required: true, message: "请输入报案城市", trigger: "blur" }],
  district: [{ required: true, message: "请输入报案区县", trigger: "blur" }],
  status: [{ required: true, message: "请选择案件状态", trigger: "change" }]
};

const dataCallback = (data: any) => ({
  list: data.list,
  total: data.total
});

const getTableList = (params: any) => getCaseRecordList(JSON.parse(JSON.stringify(params)));

const openAdd = () => {
  isEdit.value = false;
  dialogVisible.value = true;
};

const openEdit = (row: CaseRecordRow) => {
  isEdit.value = true;
  form.id = row.id;
  form.reportNumber = row.reportNumber || "";
  form.victimName = row.victimName || "";
  form.victimPhone = row.victimPhone || "";
  form.city = row.city || "";
  form.district = row.district || "";
  form.status = row.status || 1;
  dialogVisible.value = true;
};

const resetForm = () => {
  form.id = "";
  form.reportNumber = "";
  form.victimName = "";
  form.victimPhone = "";
  form.city = "";
  form.district = "";
  form.status = 1;
  isEdit.value = false;
  formRef.value?.clearValidate();
};

const submitForm = () => {
  formRef.value?.validate(async valid => {
    if (!valid) return;
    const payload = {
      reportNumber: form.reportNumber.trim(),
      victimName: form.victimName.trim(),
      victimPhone: form.victimPhone.trim(),
      city: form.city.trim(),
      district: form.district.trim(),
      status: form.status
    };
    try {
      if (isEdit.value) {
        const res = await editCaseRecord(form.id, payload);
        ElMessage.success({ message: res.msg || "编辑成功" });
      } else {
        const res = await addCaseRecord(payload);
        ElMessage.success({ message: res.msg || "新增成功" });
      }
      dialogVisible.value = false;
      proTable.value?.getTableList();
    } catch {
      /* 全局拦截器已提示错误 */
    }
  });
};

const deleteOne = async (row: CaseRecordRow) => {
  await useHandleData(deleteCaseRecord, row.id, `删除【${row.reportNumber}】案件`);
  proTable.value?.getTableList();
};

const columns = reactive<ColumnProps<CaseRecordRow>[]>([
  { type: "index", label: "#", width: 56 },
  {
    prop: "reportNumber",
    label: "出险报案号",
    minWidth: 160,
    search: { el: "input", props: { placeholder: "请输入出险报案号" } }
  },
  {
    prop: "victimName",
    label: "伤者姓名",
    minWidth: 120,
    search: { el: "input", props: { placeholder: "请输入伤者姓名" } }
  },
  {
    prop: "victimPhone",
    label: "联系电话",
    minWidth: 130
  },
  {
    prop: "city",
    label: "城市",
    minWidth: 100
  },
  {
    prop: "district",
    label: "区县",
    minWidth: 100
  },
  {
    prop: "status",
    label: "案件状态",
    width: 110,
    search: { el: "select", props: { placeholder: "请选择案件状态" } },
    enum: caseStatusOptions,
    render: scope => {
      const item = caseStatusMap[scope.row.status];
      if (!item) return "--";
      return <el-tag type={item.tagType}>{item.label}</el-tag>;
    }
  },
  {
    prop: "createdAt",
    label: "创建时间",
    width: 170
  },
  { prop: "operation", label: "操作", fixed: "right", width: 160 }
]);
</script>
