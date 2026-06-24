<template>
  <div class="table-box region-config-page">
    <ProTable ref="proTable" :columns="columns" :request-api="getTableList" :data-callback="dataCallback">
      <template #tableHeader>
        <el-button v-auth="'region:edit'" type="primary" :icon="CirclePlus" @click="openAdd">新增区域</el-button>
      </template>
      <template #operation="scope">
        <el-button v-auth="'region:edit'" type="primary" link :icon="EditPen" @click="openEdit(scope.row)">编辑</el-button>
        <el-button v-auth="'region:edit'" type="danger" link :icon="Delete" @click="deleteOne(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑区域配置' : '新增区域配置'"
      width="560px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <RegionCascader
          v-if="!isEdit"
          v-model="form.regionCascader"
          label="开放地区"
          prop="regionCascader"
          @change="onRegionChange"
        />
        <el-form-item v-else label="开放地区">
          <span>{{ editRegionText }}</span>
        </el-form-item>
        <el-form-item label="状态" prop="enabled">
          <el-radio-group v-model="form.enabled">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序" prop="sort">
          <el-input-number v-model="form.sort" :min="0" :max="9999" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="255" show-word-limit placeholder="可选" />
        </el-form-item>
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          title="配置表非空时，仅列表中启用的地区允许新建/派单；表为空时默认全国开放。"
        />
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="tsx" name="regionConfig">
import { reactive, ref } from "vue";
import { CirclePlus, Delete, EditPen } from "@element-plus/icons-vue";
import { ElMessage, FormInstance } from "element-plus";
import type { FormRules } from "element-plus";
import ProTable from "@/components/ProTable/index.vue";
import RegionCascader from "@/components/RegionCascader/index.vue";
import { ColumnProps, ProTableInstance } from "@/components/ProTable/interface";
import {
  addRegionConfig,
  deleteRegionConfig,
  editRegionConfig,
  getRegionConfigList,
  type RegionConfigRow
} from "@/api/modules/bizRegion";
import { REGION_ENABLED_OPTIONS } from "@/constants/business";
import { useHandleData } from "@/hooks/useHandleData";
import { validateRegion } from "@/utils/region";

const proTable = ref<ProTableInstance>();
const dialogVisible = ref(false);
const isEdit = ref(false);
const editId = ref("");
const editRegionText = ref("");
const submitLoading = ref(false);
const formRef = ref<FormInstance>();

const form = reactive({
  province: "",
  city: "",
  district: "",
  regionCascader: [] as string[],
  enabled: 1,
  sort: 0,
  remark: ""
});

const rules: FormRules = {
  regionCascader: [{ required: true, validator: validateRegion, trigger: "change" }],
  enabled: [{ required: true, message: "请选择状态", trigger: "change" }]
};

const dataCallback = (data: { list: RegionConfigRow[]; total: number }) => ({
  list: data.list,
  total: data.total
});

const getTableList = (params: Record<string, unknown>) => getRegionConfigList(params as any);

const onRegionChange = (_value: string[], fields: { province: string; city: string; district: string }) => {
  form.province = fields.province;
  form.city = fields.city;
  form.district = fields.district;
};

const resetForm = () => {
  isEdit.value = false;
  editId.value = "";
  editRegionText.value = "";
  form.province = "";
  form.city = "";
  form.district = "";
  form.regionCascader = [];
  form.enabled = 1;
  form.sort = 0;
  form.remark = "";
  formRef.value?.resetFields();
};

const openAdd = () => {
  resetForm();
  dialogVisible.value = true;
};

const openEdit = (row: RegionConfigRow) => {
  isEdit.value = true;
  editId.value = row.id;
  editRegionText.value = row.regionText;
  form.enabled = row.enabled;
  form.sort = row.sort;
  form.remark = row.remark || "";
  dialogVisible.value = true;
};

const submitForm = async () => {
  if (!formRef.value) return;
  if (!isEdit.value) {
    await formRef.value.validate();
  }
  submitLoading.value = true;
  try {
    if (isEdit.value) {
      await editRegionConfig(editId.value, {
        enabled: form.enabled,
        sort: form.sort,
        remark: form.remark
      });
      ElMessage.success("修改成功");
    } else {
      await addRegionConfig({
        province: form.province,
        city: form.city,
        district: form.district,
        enabled: form.enabled,
        sort: form.sort,
        remark: form.remark
      });
      ElMessage.success("新增成功");
    }
    dialogVisible.value = false;
    proTable.value?.getTableList();
  } finally {
    submitLoading.value = false;
  }
};

const deleteOne = async (row: RegionConfigRow) => {
  await useHandleData(deleteRegionConfig, row.id, `删除【${row.regionText}】区域配置`);
  proTable.value?.getTableList();
};

const columns = reactive<ColumnProps<RegionConfigRow>[]>([
  { type: "index", label: "#", width: 56 },
  { prop: "regionText", label: "开放地区", minWidth: 220 },
  {
    prop: "enabled",
    label: "状态",
    width: 100,
    enum: REGION_ENABLED_OPTIONS,
    search: { el: "select", props: { placeholder: "状态", clearable: true } },
    render: scope => {
      const item = REGION_ENABLED_OPTIONS.find(opt => opt.value === scope.row.enabled);
      return <el-tag type={scope.row.enabled === 1 ? "success" : "info"}>{item?.label || "—"}</el-tag>;
    }
  },
  { prop: "sort", label: "排序", width: 80 },
  { prop: "remark", label: "备注", minWidth: 140, showOverflowTooltip: true },
  { prop: "updatedAt", label: "更新时间", width: 170 },
  { prop: "operation", label: "操作", fixed: "right", width: 140 }
]);
</script>
