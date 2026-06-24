<template>
  <div class="table-box agency-scope-page">
    <ProTable
      ref="proTable"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
      :init-param="tableInitParam"
    >
      <template #tableHeader>
        <el-button v-auth="'agency:scope:edit'" type="primary" :icon="CirclePlus" @click="openAdd">新增合作范围</el-button>
      </template>
      <template #operation="scope">
        <el-button v-auth="'agency:scope:edit'" type="danger" link :icon="Delete" @click="deleteOne(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <el-dialog v-model="dialogVisible" title="新增合作范围" width="560px" destroy-on-close @closed="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="鉴定机构" prop="agencyId">
          <el-select v-model="form.agencyId" placeholder="请选择机构" filterable clearable style="width: 100%">
            <el-option v-for="item in agencyOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <RegionCascader v-model="form.regionCascader" label="服务地区" prop="regionCascader" @change="onRegionChange" />
        <el-alert type="info" :closable="false" show-icon title="未配置合作范围的机构，自动派单时仍按机构办公地址匹配。" />
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="tsx" name="agencyScope">
import { onMounted, reactive, ref } from "vue";
import { CirclePlus, Delete } from "@element-plus/icons-vue";
import { ElMessage, FormInstance } from "element-plus";
import type { FormRules } from "element-plus";
import ProTable from "@/components/ProTable/index.vue";
import RegionCascader from "@/components/RegionCascader/index.vue";
import { ColumnProps, ProTableInstance } from "@/components/ProTable/interface";
import {
  addAgencyServiceScope,
  deleteAgencyServiceScope,
  getAgencyOptions,
  getAgencyServiceScopeList,
  type AgencyServiceScopeRow
} from "@/api/modules/bizAgency";
import { useHandleData } from "@/hooks/useHandleData";
import { validateRegion } from "@/utils/region";

const proTable = ref<ProTableInstance>();
const tableInitParam = {};
const agencyOptions = ref<{ label: string; value: number }[]>([]);

const dialogVisible = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const form = reactive({
  agencyId: undefined as number | undefined,
  province: "",
  city: "",
  district: "",
  regionCascader: [] as string[]
});

const rules: FormRules = {
  agencyId: [{ required: true, message: "请选择机构", trigger: "change" }],
  regionCascader: [{ required: true, validator: validateRegion, trigger: "change" }]
};

onMounted(async () => {
  const res = await getAgencyOptions();
  agencyOptions.value = (res.data.list || []).map(item => ({
    label: item.agencyName,
    value: Number(item.id)
  }));
});

const dataCallback = (data: { list: AgencyServiceScopeRow[]; total: number }) => ({
  list: data.list,
  total: data.total
});

const getTableList = (params: Record<string, unknown>) => getAgencyServiceScopeList(params as any);

const onRegionChange = (_value: string[], fields: { province: string; city: string; district: string }) => {
  form.province = fields.province;
  form.city = fields.city;
  form.district = fields.district;
};

const openAdd = () => {
  dialogVisible.value = true;
};

const resetForm = () => {
  form.agencyId = undefined;
  form.province = "";
  form.city = "";
  form.district = "";
  form.regionCascader = [];
  formRef.value?.resetFields();
};

const submitForm = async () => {
  if (!formRef.value) return;
  await formRef.value.validate();
  if (form.agencyId == null) return;
  submitLoading.value = true;
  try {
    await addAgencyServiceScope({
      agencyId: form.agencyId,
      province: form.province,
      city: form.city,
      district: form.district
    });
    ElMessage.success("新增成功");
    dialogVisible.value = false;
    proTable.value?.getTableList();
  } finally {
    submitLoading.value = false;
  }
};

const deleteOne = async (row: AgencyServiceScopeRow) => {
  await useHandleData(deleteAgencyServiceScope, row.id, `删除【${row.regionText}】合作范围`);
  proTable.value?.getTableList();
};

const columns = reactive<ColumnProps<AgencyServiceScopeRow>[]>([
  { type: "index", label: "#", width: 56 },
  {
    prop: "agencyId",
    label: "鉴定机构",
    minWidth: 160,
    isFilterEnum: false,
    enum: agencyOptions,
    search: { el: "select", props: { placeholder: "请选择机构", filterable: true, clearable: true } },
    render: scope => scope.row.agencyName || "—"
  },
  { prop: "regionText", label: "服务地区", minWidth: 220 },
  { prop: "createdAt", label: "创建时间", width: 170 },
  { prop: "operation", label: "操作", fixed: "right", width: 100 }
]);
</script>
