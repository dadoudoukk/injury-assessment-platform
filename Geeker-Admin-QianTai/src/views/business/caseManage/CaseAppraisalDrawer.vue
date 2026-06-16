<template>
  <el-drawer v-model="visible" title="查看鉴定结果" size="min(720px, 96vw)" destroy-on-close @closed="onClosed">
    <div v-loading="loading" class="appraisal-drawer-body">
      <el-descriptions v-if="detail.reportNumber" :column="2" border class="case-summary">
        <el-descriptions-item label="出险报案号">{{ detail.reportNumber }}</el-descriptions-item>
        <el-descriptions-item label="伤者姓名">{{ detail.victimName }}</el-descriptions-item>
        <el-descriptions-item v-if="!isAgencyMode" label="鉴定机构" :span="2">
          {{ detail.agencyName || "暂未指派" }}
        </el-descriptions-item>
        <el-descriptions-item v-if="detail.documentNumber" label="鉴定文书编号" :span="2">
          {{ detail.documentNumber }}
        </el-descriptions-item>
      </el-descriptions>

      <template v-if="detail.appraisalVideos?.length">
        <div class="section-title">鉴定取证视频</div>
        <ul class="video-list">
          <li v-for="(video, index) in detail.appraisalVideos" :key="index">
            <el-link :href="video.url" target="_blank" type="primary">
              {{ video.name || `视频 ${index + 1}` }}
            </el-link>
          </li>
        </ul>
      </template>

      <template v-if="detail.electronicCertificate?.url">
        <div class="section-title">电子证书</div>
        <ul class="video-list">
          <li>
            <el-link :href="detail.electronicCertificate.url" target="_blank" type="primary">
              {{ detail.electronicCertificate.name || "电子证书.pdf" }}
            </el-link>
          </li>
        </ul>
      </template>

      <template v-if="detail.appraisalAmount || detail.appraisalConclusion">
        <div class="section-title">历史鉴定报告（只读）</div>
        <el-descriptions :column="1" border>
          <el-descriptions-item v-if="detail.appraisalAmount" label="理赔金额">
            ¥{{ detail.appraisalAmount }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detail.appraisalConclusion" label="鉴定结论">
            {{ detail.appraisalConclusion }}
          </el-descriptions-item>
        </el-descriptions>
      </template>

      <template v-if="detail.reportFiles?.length">
        <div class="section-title">历史报告附件（只读）</div>
        <ul class="video-list">
          <li v-for="(file, index) in detail.reportFiles" :key="index">
            <el-link :href="file.url" target="_blank" type="primary">
              {{ file.name || `附件 ${index + 1}` }}
            </el-link>
          </li>
        </ul>
      </template>

      <el-empty v-if="!hasAnyContent" description="暂无鉴定结果数据" />
    </div>
  </el-drawer>
</template>

<script setup lang="ts" name="CaseAppraisalDrawer">
import { computed, reactive, ref } from "vue";
import { getCaseRecordDetail, type CaseRecordRow } from "@/api/modules/bizCase";
import { useTenantMode } from "@/hooks/useTenantMode";
import type { AppraisalDrawerMode } from "./useCaseActions";

const { isAgencyMode } = useTenantMode();

interface AppraisalDrawerParams {
  mode: AppraisalDrawerMode;
  caseId: string;
  refresh?: () => void;
}

const visible = ref(false);
const loading = ref(false);
const drawerParams = ref<AppraisalDrawerParams | null>(null);

const detail = reactive<Partial<CaseRecordRow>>({});

const hasAnyContent = computed(
  () =>
    !!detail.documentNumber ||
    (detail.appraisalVideos?.length ?? 0) > 0 ||
    !!detail.electronicCertificate?.url ||
    !!detail.appraisalAmount ||
    !!detail.appraisalConclusion ||
    (detail.reportFiles?.length ?? 0) > 0
);

const resetDetail = () => {
  Object.keys(detail).forEach(key => {
    delete (detail as Record<string, unknown>)[key];
  });
};

const loadDetail = async (caseId: string) => {
  loading.value = true;
  try {
    const res = await getCaseRecordDetail(caseId);
    Object.assign(detail, res.data);
  } catch {
    visible.value = false;
  } finally {
    loading.value = false;
  }
};

const acceptParams = async (params: AppraisalDrawerParams) => {
  drawerParams.value = params;
  resetDetail();
  visible.value = true;
  await loadDetail(params.caseId);
};

const onClosed = () => {
  drawerParams.value = null;
  resetDetail();
};

defineExpose({ acceptParams });
</script>

<style scoped lang="scss">
.appraisal-drawer-body {
  min-height: 200px;
}
.case-summary {
  margin-bottom: 20px;
}
.section-title {
  margin: 16px 0 8px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.video-list {
  margin: 0;
  padding-left: 20px;
  li {
    margin-bottom: 8px;
  }
}
</style>
