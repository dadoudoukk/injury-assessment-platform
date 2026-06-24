<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
      :init-param="tableInitParam"
    >
      <template #tableHeader>
        <el-button v-auth="'agency:add'" type="primary" :icon="CirclePlus" @click="openAdd"> 新增机构 </el-button>
      </template>
      <template #operation="scope">
        <el-button v-auth="'agency:edit'" type="primary" link :icon="EditPen" @click="openEdit(scope.row)">编辑</el-button>
        <el-button v-auth="'agency:delete'" type="danger" link :icon="Delete" @click="deleteOne(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑鉴定机构' : '新增鉴定机构'"
      width="640px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" v-loading="formLoading" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="机构名称" prop="agencyName">
          <el-input v-model="form.agencyName" placeholder="请输入机构名称" clearable maxlength="100" />
        </el-form-item>
        <el-form-item label="联系人" prop="contactPerson">
          <el-input v-model="form.contactPerson" placeholder="请输入联系人" clearable maxlength="50" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contactPhone">
          <el-input v-model="form.contactPhone" placeholder="手机号或座机（如 010-12345678）" clearable maxlength="20" />
        </el-form-item>
        <RegionCascader v-model="form.regionCascader" label="所在地区" prop="regionCascader" @change="onRegionChange" />
        <el-form-item label="详细地址" prop="address">
          <el-input
            v-model="form.address"
            type="textarea"
            :rows="2"
            placeholder="请输入详细地址"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>
        <el-alert
          v-if="isEdit && editOriginalStatus === 3"
          type="warning"
          :closable="false"
          show-icon
          title="该机构当前为审核驳回状态，保存修改后将重新进入待审核流程。"
          class="resubmit-tip"
        />
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="tsx" name="agencyManage">
import { computed, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { CirclePlus, Delete, EditPen } from "@element-plus/icons-vue";
import { ElMessage, FormInstance } from "element-plus";
import type { FormRules } from "element-plus";
import ProTable from "@/components/ProTable/index.vue";
import RegionCascader from "@/components/RegionCascader/index.vue";
import { ColumnProps, ProTableInstance } from "@/components/ProTable/interface";
import {
  addAgency,
  deleteAgency,
  editAgency,
  getAgencyDetail,
  getAgencyList,
  type AgencyForm,
  type AgencyRow
} from "@/api/modules/bizAgency";
import { AGENCY_STATUS_OPTIONS, agencyStatusMap } from "@/constants/business";
import { useHandleData } from "@/hooks/useHandleData";
import { decodeRegion, encodeRegion, formatRegionText, validateRegion } from "@/utils/region";

/**
 * 大陆手机号 或 带/不带区号的座机
 * - 手机：1[3-9] + 9 位
 * - 座机：可选 0xx/0xxx 区号 + 7~8 位号码，区号与号码间可有 - 或空格
 * - 座机：(0xx)xxxxxxx 形式
 */
const CONTACT_PHONE_REGEX = /^(?:1[3-9]\d{9}|(?:0\d{2,3}[-\s]?)?\d{7,8}|\(0\d{2,3}\)\d{7,8})$/;

const route = useRoute();
const isArchivePage = computed(() => route.name === "agencyManage");
const isOnboardAuditPage = computed(() => route.name === "agencyOnboardAudit");
const tableInitParam = computed(() => {
  if (isArchivePage.value) return { excludeStatus: 0 };
  return {};
});

const proTable = ref<ProTableInstance>();
const dialogVisible = ref(false);
const isEdit = ref(false);
const editOriginalStatus = ref<number | null>(null);
const formRef = ref<FormInstance>();
const formLoading = ref(false);
const submitLoading = ref(false);

const form = reactive({
  id: "",
  agencyName: "",
  contactPerson: "",
  contactPhone: "",
  province: "",
  city: "",
  district: "",
  regionCascader: [] as string[],
  address: ""
});

const syncRegionToForm = (region: string[]) => {
  const { province, city, district } = encodeRegion(region);
  form.province = province;
  form.city = city;
  form.district = district;
};

const validateContactPhone = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  const phone = (value || "").trim();
  if (!phone) {
    callback(new Error("请输入联系电话"));
    return;
  }
  if (!CONTACT_PHONE_REGEX.test(phone)) {
    callback(new Error("请输入正确的手机号或座机号码"));
    return;
  }
  callback();
};

const rules: FormRules = {
  agencyName: [{ required: true, message: "请输入机构名称", trigger: "blur" }],
  contactPerson: [{ required: true, message: "请输入联系人", trigger: "blur" }],
  contactPhone: [{ required: true, validator: validateContactPhone, trigger: "blur" }],
  regionCascader: [{ required: true, validator: validateRegion, trigger: "change" }],
  address: [{ required: true, message: "请输入详细地址", trigger: "blur" }]
};

const onRegionChange = (value: string[]) => {
  syncRegionToForm(value);
};

const fillFormFromDetail = (row: AgencyRow) => {
  form.id = row.id;
  form.agencyName = row.agencyName || "";
  form.contactPerson = row.contactPerson || "";
  form.contactPhone = row.contactPhone || "";
  form.province = row.province || "";
  form.city = row.city || "";
  form.district = row.district || "";
  form.regionCascader = decodeRegion(row.province, row.city, row.district);
  form.address = row.address || "";
  editOriginalStatus.value = row.status ?? null;
};

const buildSubmitPayload = (): AgencyForm => {
  syncRegionToForm(form.regionCascader);
  return {
    agencyName: form.agencyName.trim(),
    contactPerson: form.contactPerson.trim(),
    contactPhone: form.contactPhone.trim(),
    province: form.province,
    city: form.city,
    district: form.district,
    address: form.address.trim()
  };
};

const dataCallback = (data: any) => ({
  list: data.list,
  total: data.total
});

const getTableList = (params: any) => {
  const query = { ...params };
  if (isArchivePage.value && (query.status === undefined || query.status === null || query.status === "")) {
    query.excludeStatus = 0;
  }
  return getAgencyList(query);
};

const openAdd = () => {
  isEdit.value = false;
  editOriginalStatus.value = null;
  dialogVisible.value = true;
};

const openEdit = async (row: AgencyRow) => {
  isEdit.value = true;
  dialogVisible.value = true;
  formLoading.value = true;
  try {
    const res = await getAgencyDetail(row.id);
    fillFormFromDetail(res.data);
  } catch {
    dialogVisible.value = false;
  } finally {
    formLoading.value = false;
  }
};

const resetForm = () => {
  form.id = "";
  form.agencyName = "";
  form.contactPerson = "";
  form.contactPhone = "";
  form.province = "";
  form.city = "";
  form.district = "";
  form.regionCascader = [];
  form.address = "";
  editOriginalStatus.value = null;
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
        const res = await editAgency(form.id, payload);
        ElMessage.success({ message: res.msg || "编辑成功" });
      } else {
        const res = await addAgency(payload);
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

const deleteOne = async (row: AgencyRow) => {
  await useHandleData(deleteAgency, row.id, `删除【${row.agencyName}】鉴定机构`);
  proTable.value?.getTableList();
};

const columns = computed<ColumnProps<AgencyRow>[]>(() => [
  { type: "index", label: "#", width: 56 },
  {
    prop: "agencyName",
    label: "机构名称",
    minWidth: 160,
    search: { el: "input", props: { placeholder: "请输入机构名称" } }
  },
  {
    prop: "contactPerson",
    label: "联系人",
    minWidth: 100,
    search: { el: "input", props: { placeholder: "请输入联系人" } }
  },
  { prop: "contactPhone", label: "联系电话", minWidth: 140 },
  {
    prop: "region",
    label: "省市区",
    minWidth: 200,
    render: scope => formatRegionText(scope.row.province, scope.row.city, scope.row.district) || "--"
  },
  { prop: "address", label: "详细地址", minWidth: 200, showOverflowTooltip: true },
  {
    prop: "status",
    label: "状态",
    width: 110,
    search: isOnboardAuditPage.value ? undefined : { el: "select", props: { placeholder: "请选择状态" } },
    enum: AGENCY_STATUS_OPTIONS,
    render: scope => {
      const item = agencyStatusMap[scope.row.status];
      if (!item) return "--";
      return <el-tag type={item.tagType}>{item.label}</el-tag>;
    }
  },
  {
    prop: "auditRemark",
    label: "驳回原因",
    minWidth: 160,
    showOverflowTooltip: true,
    render: scope => (scope.row.status === 3 && scope.row.auditRemark ? scope.row.auditRemark : "--")
  },
  { prop: "createdAt", label: "创建时间", width: 170 },
  { prop: "operation", label: "操作", fixed: "right", width: isOnboardAuditPage.value ? 100 : 220 }
]);

watch(
  () => route.name,
  () => {
    proTable.value?.getTableList();
  }
);
</script>

<style scoped lang="scss">
.resubmit-tip {
  margin-bottom: 8px;
}
</style>
