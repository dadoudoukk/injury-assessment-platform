<template>
  <div :class="['audit-payload', { compact }]">
    <template v-if="bizType === 'case_submit'">
      <el-descriptions v-if="hasCaseFields" :column="2" border size="small">
        <el-descriptions-item v-if="payload?.reportNumber" label="报案号">{{ payload.reportNumber }}</el-descriptions-item>
        <el-descriptions-item v-if="payload?.victimName" label="伤者姓名">{{ payload.victimName }}</el-descriptions-item>
        <el-descriptions-item v-if="payload?.victimPhone" label="联系电话">{{ payload.victimPhone }}</el-descriptions-item>
        <el-descriptions-item v-if="payload?.reportDate" label="报案日期">{{ payload.reportDate }}</el-descriptions-item>
        <el-descriptions-item v-if="regionText" label="报案地区" :span="2">{{ regionText }}</el-descriptions-item>
        <el-descriptions-item v-if="payload?.accidentType" label="事故类型">{{ payload.accidentType }}</el-descriptions-item>
        <el-descriptions-item v-if="payload?.injuryType" label="伤情类型">{{ payload.injuryType }}</el-descriptions-item>
        <el-descriptions-item v-if="payload?.insuranceCompany" label="保险公司" :span="2">
          {{ payload.insuranceCompany }}
        </el-descriptions-item>
      </el-descriptions>
      <template v-if="policyImages.length">
        <div class="payload-subtitle">保单图片</div>
        <ul class="link-list">
          <li v-for="(file, index) in policyImages" :key="`policy-${index}`">
            <el-link :href="file.url" target="_blank" type="primary">{{ file.name || `保单 ${index + 1}` }}</el-link>
          </li>
        </ul>
      </template>
      <template v-if="accidentDecisionImages.length">
        <div class="payload-subtitle">事故认定书</div>
        <ul class="link-list">
          <li v-for="(file, index) in accidentDecisionImages" :key="`accident-${index}`">
            <el-link :href="file.url" target="_blank" type="primary">{{ file.name || `事故认定书 ${index + 1}` }}</el-link>
          </li>
        </ul>
      </template>
      <template v-if="legacyAttachments.length">
        <div class="payload-subtitle">其他附件（历史兼容）</div>
        <ul class="link-list">
          <li v-for="(file, index) in legacyAttachments" :key="`legacy-${index}`">
            <el-link :href="file.url" target="_blank" type="primary">{{ file.name || `附件 ${index + 1}` }}</el-link>
          </li>
        </ul>
      </template>
    </template>

    <template v-else-if="bizType === 'agency_submit'">
      <div v-if="!compact" class="payload-package-tip">本批次为完整文书包提交</div>
      <el-descriptions v-if="payload?.documentNumber || certificate?.url" :column="1" border size="small">
        <el-descriptions-item v-if="payload?.documentNumber" label="鉴定文书编号">
          {{ payload.documentNumber }}
        </el-descriptions-item>
        <el-descriptions-item v-if="certificate?.url" label="电子证书">
          <el-link :href="certificate.url" target="_blank" type="primary">
            {{ certificate.name || "电子证书" }}
          </el-link>
        </el-descriptions-item>
      </el-descriptions>
      <template v-if="reportFiles.length">
        <div class="payload-subtitle">报告附件</div>
        <ul class="link-list">
          <li v-for="(file, index) in reportFiles" :key="index">
            <el-link :href="file.url" target="_blank" type="primary">{{ file.name || `附件 ${index + 1}` }}</el-link>
          </li>
        </ul>
      </template>
    </template>

    <template v-else-if="bizType === 'agency_onboard'">
      <el-descriptions v-if="hasAgencyFields" :column="2" border size="small">
        <el-descriptions-item v-if="payload?.agencyName" label="机构名称">{{ payload.agencyName }}</el-descriptions-item>
        <el-descriptions-item v-if="payload?.contactPerson" label="联系人">{{ payload.contactPerson }}</el-descriptions-item>
        <el-descriptions-item v-if="payload?.contactPhone" label="联系电话">{{ payload.contactPhone }}</el-descriptions-item>
        <el-descriptions-item v-if="agencyRegion" label="所在地区" :span="2">{{ agencyRegion }}</el-descriptions-item>
        <el-descriptions-item v-if="payload?.address" label="详细地址" :span="2">{{ payload.address }}</el-descriptions-item>
      </el-descriptions>
    </template>

    <el-empty v-if="!hasContent" :image-size="compact ? 48 : 80" description="本批次无提交内容" />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { AuditAttachmentItem } from "@/api/modules/bizAudit";
import type { AuditBizType } from "@/constants/audit";
import { formatRegionText } from "@/utils/region";

const props = defineProps<{
  bizType?: AuditBizType;
  payload?: Record<string, unknown> | null;
  compact?: boolean;
}>();

function attachmentKey(file: AuditAttachmentItem) {
  return `${file.url || ""}|${file.name || ""}`;
}

function normalizeFiles(raw: unknown): AuditAttachmentItem[] {
  if (!Array.isArray(raw)) return [];
  return raw.filter((item): item is AuditAttachmentItem => !!item && typeof item === "object" && !!item.url);
}

function dedupeFiles(items: AuditAttachmentItem[]) {
  const seen = new Set<string>();
  const result: AuditAttachmentItem[] = [];
  for (const item of items) {
    const key = attachmentKey(item);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(item);
  }
  return result;
}

const attachments = computed(() => normalizeFiles(props.payload?.attachments));

const policyImages = computed(() => {
  const structured = normalizeFiles(props.payload?.policyImages);
  const fromAttachments = attachments.value.filter(file => file.category === "policy");
  return dedupeFiles([...structured, ...fromAttachments]);
});

const accidentDecisionImages = computed(() => {
  const structured = normalizeFiles(props.payload?.accidentDecisionImages);
  const fromAttachments = attachments.value.filter(file => file.category === "accident_decision");
  return dedupeFiles([...structured, ...fromAttachments]);
});

const legacyAttachments = computed(() =>
  attachments.value.filter(file => file.category !== "policy" && file.category !== "accident_decision")
);

const reportFiles = computed(() => {
  const raw = props.payload?.reportFiles;
  return Array.isArray(raw) ? (raw as AuditAttachmentItem[]) : [];
});

const certificate = computed(() => {
  const raw = props.payload?.electronicCertificate;
  if (raw && typeof raw === "object" && "url" in raw) {
    return raw as { url: string; name?: string };
  }
  return null;
});

const regionText = computed(() =>
  formatRegionText(
    String(props.payload?.province || ""),
    String(props.payload?.city || ""),
    String(props.payload?.district || "")
  )
);

const agencyRegion = computed(() =>
  formatRegionText(
    String(props.payload?.province || ""),
    String(props.payload?.city || ""),
    String(props.payload?.district || "")
  )
);

const hasCaseFields = computed(
  () =>
    !!props.payload?.reportNumber ||
    !!props.payload?.victimName ||
    policyImages.value.length > 0 ||
    accidentDecisionImages.value.length > 0 ||
    legacyAttachments.value.length > 0
);

const hasAgencyFields = computed(() => !!props.payload?.agencyName || !!props.payload?.contactPerson || !!props.payload?.address);

const hasContent = computed(() => {
  if (props.bizType === "case_submit") return hasCaseFields.value;
  if (props.bizType === "agency_submit") {
    return !!props.payload?.documentNumber || !!certificate.value?.url || reportFiles.value.length > 0;
  }
  if (props.bizType === "agency_onboard") return hasAgencyFields.value;
  return false;
});
</script>

<style scoped lang="scss">
.audit-payload.compact {
  margin-top: 4px;
}
.payload-package-tip {
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.payload-subtitle {
  margin: 8px 0 4px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.link-list {
  margin: 0;
  padding-left: 18px;
  li {
    line-height: 1.8;
  }
}
</style>
