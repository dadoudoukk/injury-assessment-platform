<template>
  <div class="table-box">
    <ProTable ref="proTable" :columns="columns" :request-api="getTableList" :data-callback="dataCallback" />
  </div>
</template>

<script setup lang="tsx" name="agencyRejectLog">
import { onMounted, reactive, ref } from "vue";
import ProTable from "@/components/ProTable/index.vue";
import { ColumnProps, ProTableInstance } from "@/components/ProTable/interface";
import { getAgencyOptions, getAgencyRejectLogList, type AgencyRejectLogRow } from "@/api/modules/bizAgency";
import { CASE_STATUS_MAP } from "@/api/modules/bizCase";

const proTable = ref<ProTableInstance>();
const agencyOptions = ref<{ label: string; value: number }[]>([]);

onMounted(async () => {
  const res = await getAgencyOptions();
  agencyOptions.value = (res.data.list || []).map(item => ({
    label: item.agencyName,
    value: Number(item.id)
  }));
});

const dataCallback = (data: { list: AgencyRejectLogRow[]; total: number }) => ({
  list: data.list,
  total: data.total
});

const getTableList = (params: Record<string, unknown>) => getAgencyRejectLogList(params as any);

const columns = reactive<ColumnProps<AgencyRejectLogRow>[]>([
  { type: "index", label: "#", width: 56 },
  {
    prop: "reportNumber",
    label: "出险报案号",
    minWidth: 150,
    search: { el: "input", props: { placeholder: "请输入出险报案号" } }
  },
  { prop: "victimName", label: "伤者姓名", minWidth: 100 },
  {
    prop: "agencyId",
    label: "拒单机构",
    minWidth: 140,
    isFilterEnum: false,
    enum: agencyOptions,
    search: { el: "select", props: { placeholder: "请选择机构", filterable: true, clearable: true } },
    render: scope => scope.row.rejectedAgencyName || "—"
  },
  {
    prop: "currentAgencyName",
    label: "当前承接机构",
    minWidth: 140,
    render: scope => scope.row.currentAgencyName || "暂未指派"
  },
  {
    prop: "caseStatus",
    label: "案件状态",
    width: 120,
    render: scope => {
      const item = CASE_STATUS_MAP[scope.row.caseStatus];
      if (!item) return scope.row.caseStatusLabel || "—";
      return <el-tag type={item.tagType}>{item.label}</el-tag>;
    }
  },
  { prop: "recordTime", label: "记录时间", width: 170 }
]);
</script>
