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
      width="640px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" v-loading="formLoading" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="出险报案号" prop="reportNumber">
          <el-input v-model="form.reportNumber" placeholder="请输入出险报案号" clearable maxlength="50" />
        </el-form-item>
        <el-form-item label="伤者姓名" prop="victimName">
          <el-input v-model="form.victimName" placeholder="请输入伤者姓名" clearable maxlength="50" />
        </el-form-item>
        <el-form-item label="联系电话" prop="victimPhone">
          <el-input v-model="form.victimPhone" placeholder="请输入联系电话" clearable maxlength="20" />
        </el-form-item>
        <el-form-item label="报案日期" prop="reportDate">
          <el-date-picker
            v-model="form.reportDate"
            type="date"
            placeholder="请选择报案日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="报案地区" prop="regionCascader">
          <el-cascader
            v-model="form.regionCascader"
            :options="pcaTextArr"
            placeholder="请选择省 / 市 / 区"
            clearable
            filterable
            style="width: 100%"
            @change="onRegionChange"
          />
        </el-form-item>
        <el-form-item label="事故类型" prop="accidentType">
          <el-select v-model="form.accidentType" placeholder="请选择事故类型" clearable style="width: 100%">
            <el-option v-for="item in accidentTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="伤情类型" prop="injuryType">
          <el-select v-model="form.injuryType" placeholder="请选择伤情类型" clearable style="width: 100%">
            <el-option v-for="item in injuryTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="保险公司" prop="insuranceCompany">
          <el-select v-model="form.insuranceCompany" placeholder="请选择保险公司" clearable style="width: 100%">
            <el-option v-for="item in insuranceCompanyOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="案件状态" prop="status">
          <el-select v-model="form.status" placeholder="请选择案件状态" style="width: 100%">
            <el-option v-for="item in caseStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="tsx" name="caseManage">
import { onMounted, reactive, ref } from "vue";
import { CirclePlus, Delete, EditPen } from "@element-plus/icons-vue";
import { ElMessage, FormInstance } from "element-plus";
import type { FormRules } from "element-plus";
import { pcaTextArr } from "element-china-area-data";
import ProTable from "@/components/ProTable/index.vue";
import { ColumnProps, ProTableInstance } from "@/components/ProTable/interface";
import {
  addCaseRecord,
  deleteCaseRecord,
  editCaseRecord,
  getCaseRecordDetail,
  getCaseRecordList,
  type CaseRecordForm,
  type CaseRecordRow
} from "@/api/modules/bizCase";
import { getDictByCode, type DictOption } from "@/api/modules/dict";
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

/** 省市区 cascader 数组 → 三个独立字段 */
const encodeRegion = (region: string[]) => ({
  province: region[0]?.trim() || "",
  city: region[1]?.trim() || "",
  district: region[2]?.trim() || ""
});

/** 三个独立字段 → cascader 回显数组 */
const decodeRegion = (province?: string, city?: string, district?: string): string[] => {
  const arr: string[] = [];
  if (province?.trim()) arr.push(province.trim());
  if (city?.trim()) arr.push(city.trim());
  if (district?.trim()) arr.push(district.trim());
  return arr;
};

const syncRegionToForm = (region: string[]) => {
  const { province, city, district } = encodeRegion(region);
  form.province = province;
  form.city = city;
  form.district = district;
};

const proTable = ref<ProTableInstance>();
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();
const formLoading = ref(false);
const submitLoading = ref(false);

const accidentTypeOptions = ref<DictOption[]>([]);
const injuryTypeOptions = ref<DictOption[]>([]);
const insuranceCompanyOptions = ref<DictOption[]>([]);

const form = reactive({
  id: "",
  reportNumber: "",
  victimName: "",
  victimPhone: "",
  reportDate: "",
  province: "",
  city: "",
  district: "",
  regionCascader: [] as string[],
  accidentType: "",
  injuryType: "",
  insuranceCompany: "",
  status: 1
});

onMounted(async () => {
  const [accidentRes, injuryRes, insuranceRes] = await Promise.all([
    getDictByCode("biz_accident_type"),
    getDictByCode("biz_injury_type"),
    getDictByCode("biz_insurance_company")
  ]);
  accidentTypeOptions.value = accidentRes.data;
  injuryTypeOptions.value = injuryRes.data;
  insuranceCompanyOptions.value = insuranceRes.data;
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

const validateRegion = (_rule: unknown, value: string[], callback: (error?: Error) => void) => {
  if (!value || value.length < 3) {
    callback(new Error("请选择完整的省 / 市 / 区"));
    return;
  }
  callback();
};

const rules: FormRules = {
  reportNumber: [{ required: true, message: "请输入出险报案号", trigger: "blur" }],
  victimName: [{ required: true, message: "请输入伤者姓名", trigger: "blur" }],
  victimPhone: [{ required: true, validator: validatePhone, trigger: "blur" }],
  reportDate: [{ required: true, message: "请选择报案日期", trigger: "change" }],
  regionCascader: [{ required: true, validator: validateRegion, trigger: "change" }],
  accidentType: [{ required: true, message: "请选择事故类型", trigger: "change" }],
  injuryType: [{ required: true, message: "请选择伤情类型", trigger: "change" }],
  insuranceCompany: [{ required: true, message: "请选择保险公司", trigger: "change" }],
  status: [{ required: true, message: "请选择案件状态", trigger: "change" }]
};

const onRegionChange = (value: string[] | null | undefined) => {
  syncRegionToForm(value || []);
};

const fillFormFromRow = (row: CaseRecordRow) => {
  form.id = row.id;
  form.reportNumber = row.reportNumber || "";
  form.victimName = row.victimName || "";
  form.victimPhone = row.victimPhone || "";
  form.reportDate = row.reportDate || "";
  form.province = row.province || "";
  form.city = row.city || "";
  form.district = row.district || "";
  form.regionCascader = decodeRegion(row.province, row.city, row.district);
  form.accidentType = row.accidentType || "";
  form.injuryType = row.injuryType || "";
  form.insuranceCompany = row.insuranceCompany || "";
  form.status = row.status || 1;
};

const buildSubmitPayload = (): CaseRecordForm => {
  syncRegionToForm(form.regionCascader);
  return {
    reportNumber: form.reportNumber.trim(),
    victimName: form.victimName.trim(),
    victimPhone: form.victimPhone.trim(),
    reportDate: form.reportDate,
    province: form.province,
    city: form.city,
    district: form.district,
    accidentType: form.accidentType,
    injuryType: form.injuryType,
    insuranceCompany: form.insuranceCompany,
    status: form.status
  };
};

const dataCallback = (data: any) => ({
  list: data.list,
  total: data.total
});

/** 将 ProTable 搜索中的 reportDate 日期范围数组拆解为后端 Query 参数 */
const formatListParams = (params: Record<string, any>) => {
  const newParams = { ...params };
  const reportDateRange = newParams.reportDate;
  if (Array.isArray(reportDateRange) && reportDateRange.length === 2) {
    newParams.reportDateStart = reportDateRange[0];
    newParams.reportDateEnd = reportDateRange[1];
  }
  delete newParams.reportDate;
  return newParams;
};

const getTableList = (params: any) => {
  const formatted = formatListParams(JSON.parse(JSON.stringify(params)));
  return getCaseRecordList(formatted);
};

const openAdd = () => {
  isEdit.value = false;
  dialogVisible.value = true;
};

const openEdit = async (row: CaseRecordRow) => {
  isEdit.value = true;
  dialogVisible.value = true;
  formLoading.value = true;
  try {
    const res = await getCaseRecordDetail(row.id);
    fillFormFromRow(res.data);
  } catch {
    dialogVisible.value = false;
  } finally {
    formLoading.value = false;
  }
};

const resetForm = () => {
  form.id = "";
  form.reportNumber = "";
  form.victimName = "";
  form.victimPhone = "";
  form.reportDate = "";
  form.province = "";
  form.city = "";
  form.district = "";
  form.regionCascader = [];
  form.accidentType = "";
  form.injuryType = "";
  form.insuranceCompany = "";
  form.status = 1;
  isEdit.value = false;
  formRef.value?.clearValidate();
};

const submitForm = () => {
  formRef.value?.validate(async valid => {
    if (!valid) return;
    const payload = buildSubmitPayload();
    submitLoading.value = true;
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
    } finally {
      submitLoading.value = false;
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
    minWidth: 150,
    search: { el: "input", props: { placeholder: "请输入出险报案号" } }
  },
  {
    prop: "reportDate",
    label: "报案日期",
    width: 120,
    search: {
      el: "date-picker",
      span: 2,
      props: { type: "daterange", valueFormat: "YYYY-MM-DD" }
    }
  },
  { prop: "province", label: "省", minWidth: 90 },
  { prop: "city", label: "市", minWidth: 90 },
  { prop: "district", label: "区", minWidth: 90 },
  {
    prop: "victimName",
    label: "伤者姓名",
    minWidth: 100,
    search: { el: "input", props: { placeholder: "请输入伤者姓名" } }
  },
  { prop: "victimPhone", label: "联系电话", minWidth: 130 },
  { prop: "accidentType", label: "事故类型", minWidth: 100 },
  { prop: "injuryType", label: "伤情类型", minWidth: 90 },
  {
    prop: "insuranceCompany",
    label: "保险公司",
    minWidth: 110,
    isFilterEnum: false,
    enum: () => getDictByCode("biz_insurance_company"),
    search: { el: "select", props: { placeholder: "请选择保险公司", filterable: true } }
  },
  {
    prop: "status",
    label: "案件状态",
    width: 100,
    search: { el: "select", props: { placeholder: "请选择案件状态" } },
    enum: caseStatusOptions,
    render: scope => {
      const item = caseStatusMap[scope.row.status];
      if (!item) return "--";
      return <el-tag type={item.tagType}>{item.label}</el-tag>;
    }
  },
  { prop: "operation", label: "操作", fixed: "right", width: 160 }
]);
</script>
