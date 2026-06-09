<template>
  <div class="table-box">
    <ProTable ref="proTable" :columns="columns" :request-api="getTableList" :data-callback="dataCallback">
      <template #tableHeader>
        <el-button v-if="canAddCase" type="primary" :icon="CirclePlus" @click="openAdd">新增案件</el-button>
        <el-button type="warning" plain :icon="Download" @click="downloadFile">导出案件</el-button>
      </template>
      <template #operation="scope">
        <el-button
          v-for="action in getCaseRowActions(scope.row)"
          :key="action.key"
          :type="action.type ?? 'primary'"
          link
          :icon="action.icon"
          @click="action.onClick(scope.row)"
        >
          {{ action.label }}
        </el-button>
      </template>
    </ProTable>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px" destroy-on-close @closed="resetForm">
      <el-form
        ref="formRef"
        v-loading="formLoading"
        :model="form"
        :rules="isFormReadonly ? undefined : rules"
        :disabled="isFormReadonly"
        :hide-required-asterisk="isFormReadonly"
        label-width="110px"
      >
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
        <RegionCascader
          v-model="form.regionCascader"
          label="报案地区"
          prop="regionCascader"
          :disabled="isFormReadonly"
          @change="onRegionChange"
        />
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
        <el-form-item v-if="!isAgencyMode" label="鉴定机构" prop="agencyId">
          <el-select
            v-model="form.agencyId"
            :placeholder="isEdit ? '请选择鉴定机构（可清空）' : '不选将自动就近派单'"
            clearable
            filterable
            style="width: 100%"
          >
            <el-option v-for="item in agencySelectOptions" :key="item.id" :label="item.agencyName" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isFormReadonly && isEdit" label="案件状态" prop="status">
          <el-select v-model="form.status" placeholder="请选择案件状态" style="width: 100%" disabled>
            <el-option v-for="item in caseStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template v-if="!isFormReadonly" #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reworkDialogVisible" title="复议 / 打回修改" width="500px" destroy-on-close>
      <el-form :model="reworkForm" ref="reworkFormRef" :rules="reworkRules" label-width="80px">
        <el-form-item label="打回原因" prop="remark">
          <el-input
            v-model="reworkForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入打回重做原因或复议意见"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reworkDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="reworkLoading" @click="submitRework">确认打回</el-button>
      </template>
    </el-dialog>

    <CaseAppraisalDrawer ref="appraisalDrawerRef" />
  </div>
</template>

<script setup lang="tsx" name="caseManage">
import { computed, onMounted, reactive, ref } from "vue";
import { CirclePlus } from "@element-plus/icons-vue";
import { ElMessage, FormInstance } from "element-plus";
import type { FormRules } from "element-plus";
import ProTable from "@/components/ProTable/index.vue";
import RegionCascader from "@/components/RegionCascader/index.vue";
import { ColumnProps, ProTableInstance } from "@/components/ProTable/interface";
import { Download } from "@element-plus/icons-vue";
import { useDownload } from "@/hooks/useDownload";
import {
  addCaseRecord,
  deleteCaseRecord,
  editCaseRecord,
  exportCaseRecord,
  reworkCaseRecord,
  getCaseRecordDetail,
  getCaseRecordList,
  type CaseRecordForm,
  type CaseRecordRow
} from "@/api/modules/bizCase";
import { getAgencyOptions, type AgencyOption } from "@/api/modules/bizAgency";
import { getDictByCode, type DictOption } from "@/api/modules/dict";
import { getInsuranceAll } from "@/api/modules/bizInsurance";
import { useHandleData } from "@/hooks/useHandleData";
import { useTenantMode } from "@/hooks/useTenantMode";
import { decodeRegion, encodeRegion, formatRegionText, validateRegion } from "@/utils/region";
import CaseAppraisalDrawer from "./CaseAppraisalDrawer.vue";
import { useCaseActions, type AppraisalDrawerMode } from "./useCaseActions";

const caseStatusOptions = [
  { label: "待接单", value: 1, tagType: "warning" },
  { label: "鉴定中", value: 2, tagType: "primary" },
  { label: "已完成", value: 3, tagType: "success" },
  { label: "已打回", value: 4, tagType: "danger" }
];

const caseStatusMap: Record<number, { label: string; tagType: string }> = {
  1: { label: "待接单", tagType: "warning" },
  2: { label: "鉴定中", tagType: "primary" },
  3: { label: "已完成", tagType: "success" },
  4: { label: "已打回", tagType: "danger" }
};

const ORPHAN_AGENCY_SUFFIX = " (已不可用)";

const { isAgencyMode } = useTenantMode();

const proTable = ref<ProTableInstance>();
const appraisalDrawerRef = ref<InstanceType<typeof CaseAppraisalDrawer> | null>(null);
const dialogVisible = ref(false);
const isEdit = ref(false);
const isView = ref(false);
const formRef = ref<FormInstance>();
const formLoading = ref(false);
const submitLoading = ref(false);

const dialogTitle = computed(() => {
  if (isView.value) return "案件详情";
  return isEdit.value ? "编辑案件" : "新增案件";
});

const accidentTypeOptions = ref<DictOption[]>([]);
const injuryTypeOptions = ref<DictOption[]>([]);
const insuranceCompanyOptions = ref<DictOption[]>([]);
const agencyOptions = ref<AgencyOption[]>([]);
/** 编辑弹窗内下拉选项（含孤儿临时项） */
const agencySelectOptions = ref<AgencyOption[]>([]);

const agencySearchEnum = computed(() =>
  agencyOptions.value.map(item => ({
    label: item.agencyName,
    value: Number(item.id)
  }))
);

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
  status: 1,
  agencyId: "" as string
});

onMounted(async () => {
  const [accidentRes, injuryRes, insuranceRes, agencyRes] = await Promise.all([
    getDictByCode("biz_accident_type"),
    getDictByCode("biz_injury_type"),
    getInsuranceAll(),
    getAgencyOptions()
  ]);
  accidentTypeOptions.value = accidentRes.data;
  injuryTypeOptions.value = injuryRes.data;
  insuranceCompanyOptions.value = (insuranceRes.data || []).map(item => ({
    label: item.companyName,
    value: item.companyName
  }));
  agencyOptions.value = agencyRes.data.list || [];
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
  reportDate: [{ required: true, message: "请选择报案日期", trigger: "change" }],
  regionCascader: [{ required: true, validator: validateRegion, trigger: "change" }],
  accidentType: [{ required: true, message: "请选择事故类型", trigger: "change" }],
  injuryType: [{ required: true, message: "请选择伤情类型", trigger: "change" }],
  insuranceCompany: [{ required: true, message: "请选择保险公司", trigger: "change" }],
  status: [{ required: true, message: "请选择案件状态", trigger: "change" }]
};

const syncRegionToForm = (region: string[]) => {
  const { province, city, district } = encodeRegion(region);
  form.province = province;
  form.city = city;
  form.district = district;
};

const onRegionChange = (value: string[]) => {
  syncRegionToForm(value);
};

const resetAgencySelectOptions = () => {
  agencySelectOptions.value = agencyOptions.value.map(item => ({ ...item }));
};

/** 孤儿机构：当前 agencyId 不在正常 options 中时，注入临时选项供回显与改选 */
const applyAgencyToForm = (agencyId?: number | null, agencyName?: string | null) => {
  resetAgencySelectOptions();
  if (agencyId == null) {
    form.agencyId = "";
    return;
  }
  const idStr = String(agencyId);
  form.agencyId = idStr;
  const inOptions = agencySelectOptions.value.some(item => item.id === idStr);
  if (!inOptions) {
    const baseName = (agencyName || "未知机构").replace(ORPHAN_AGENCY_SUFFIX, "");
    agencySelectOptions.value.unshift({
      id: idStr,
      agencyName: `${baseName}${ORPHAN_AGENCY_SUFFIX}`
    });
  }
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
  applyAgencyToForm(row.agencyId, row.agencyName);
};

const resolveAgencyIdForSubmit = (): number | null => {
  const raw = form.agencyId?.trim();
  if (!raw) return null;
  const num = Number(raw);
  return Number.isFinite(num) ? num : null;
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
    status: form.status,
    agencyId: resolveAgencyIdForSubmit()
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

const downloadFile = async () => {
  const params = proTable.value?.searchParam || {};
  const formatted = formatListParams(JSON.parse(JSON.stringify(params)));
  useDownload(exportCaseRecord, "案件列表", formatted);
};

const openAdd = () => {
  if (isAgencyMode.value) {
    ElMessage.error("无权操作");
    return;
  }
  isEdit.value = false;
  isView.value = false;
  resetAgencySelectOptions();
  dialogVisible.value = true;
};

const openEdit = async (row: CaseRecordRow) => {
  if (isAgencyMode.value) {
    ElMessage.error("无权操作");
    return;
  }
  isEdit.value = true;
  isView.value = false;
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

const openViewDetail = async (row: CaseRecordRow) => {
  isEdit.value = true;
  isView.value = true;
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

const openAppraisalDrawer = (row: CaseRecordRow, mode: AppraisalDrawerMode) => {
  appraisalDrawerRef.value?.acceptParams({
    mode,
    caseId: row.id,
    refresh: () => proTable.value?.getTableList()
  });
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
  form.agencyId = "";
  resetAgencySelectOptions();
  isEdit.value = false;
  isView.value = false;
  formRef.value?.clearValidate();
};

const submitForm = () => {
  if (isFormReadonly.value) return;
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

const reworkDialogVisible = ref(false);
const reworkLoading = ref(false);
const reworkFormRef = ref<FormInstance>();
const reworkForm = reactive({
  id: "",
  remark: ""
});
const reworkRules = reactive<FormRules>({
  remark: [{ required: true, message: "请输入打回原因", trigger: "blur" }]
});

const openRework = (row: CaseRecordRow) => {
  reworkForm.id = row.id;
  reworkForm.remark = "";
  reworkDialogVisible.value = true;
};

const submitRework = async () => {
  if (!reworkFormRef.value) return;
  await reworkFormRef.value.validate();

  reworkLoading.value = true;
  try {
    await reworkCaseRecord(reworkForm.id, { remark: reworkForm.remark });
    ElMessage.success("案件已打回");
    reworkDialogVisible.value = false;
    proTable.value?.getTableList();
  } finally {
    reworkLoading.value = false;
  }
};

const { getCaseRowActions, canAddCase } = useCaseActions({
  openEdit,
  openViewDetail,
  openAppraisalDrawer,
  deleteOne,
  openRework
});

const isFormReadonly = computed(() => isView.value || isAgencyMode.value);

const baseColumns: ColumnProps<CaseRecordRow>[] = [
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
  {
    prop: "region",
    label: "报案地区",
    minWidth: 180,
    render: scope => formatRegionText(scope.row.province, scope.row.city, scope.row.district) || "--"
  },
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
    enum: async () => {
      const res = await getInsuranceAll();
      return {
        data: (res.data || []).map(item => ({
          label: item.companyName,
          value: item.companyName
        }))
      };
    },
    search: { el: "select", props: { placeholder: "请选择保险公司", filterable: true } }
  },
  {
    prop: "agencyId",
    label: "鉴定机构",
    minWidth: 140,
    isFilterEnum: false,
    enum: agencySearchEnum,
    search: { el: "select", props: { placeholder: "请选择鉴定机构", filterable: true, clearable: true } },
    render: scope => scope.row.agencyName || "暂未指派"
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
  { prop: "operation", label: "操作", fixed: "right", width: 280 }
];

const columns = computed(() => {
  if (isAgencyMode.value) {
    return baseColumns.filter(col => col.prop !== "agencyId");
  }
  return baseColumns;
});
</script>
