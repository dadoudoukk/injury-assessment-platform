<template>
  <el-form-item :label="label" :prop="prop" :required="required">
    <el-cascader
      :model-value="modelValue"
      :options="pcaTextArr"
      :placeholder="placeholder"
      :clearable="clearable"
      :filterable="filterable"
      :disabled="disabled"
      :style="{ width: '100%' }"
      @update:model-value="onCascaderUpdate"
    />
  </el-form-item>
</template>

<script setup lang="ts" name="RegionCascader">
import { pcaTextArr } from "element-china-area-data";
import { encodeRegion, type RegionFields } from "@/utils/region";

interface RegionCascaderProps {
  label?: string;
  prop?: string;
  placeholder?: string;
  clearable?: boolean;
  filterable?: boolean;
  disabled?: boolean;
  required?: boolean;
}

withDefaults(defineProps<RegionCascaderProps>(), {
  label: "所在地区",
  prop: "regionCascader",
  placeholder: "请选择省 / 市 / 区",
  clearable: true,
  filterable: true,
  disabled: false,
  required: true
});

/** 级联选中值：省、市、区名称数组 */
const modelValue = defineModel<string[]>({ default: () => [] });

const emit = defineEmits<{
  change: [value: string[], fields: RegionFields];
}>();

const onCascaderUpdate = (value: string[] | null | undefined) => {
  const next = value || [];
  modelValue.value = next;
  emit("change", next, encodeRegion(next));
};
</script>
