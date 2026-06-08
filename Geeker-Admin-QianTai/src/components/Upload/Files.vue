<template>
  <div class="upload-box">
    <el-upload
      v-model:file-list="_fileList"
      action="#"
      list-type="picture-card"
      :class="['upload', self_disabled ? 'disabled' : '', drag ? 'no-border' : '']"
      :multiple="true"
      :disabled="self_disabled"
      :limit="limit"
      :http-request="handleHttpUpload"
      :before-upload="beforeUpload"
      :on-exceed="handleExceed"
      :on-success="uploadSuccess"
      :on-error="uploadError"
      :drag="drag"
      :accept="accept"
    >
      <div class="upload-empty">
        <slot name="empty">
          <el-icon><Plus /></el-icon>
        </slot>
      </div>
      <template #file="{ file }">
        <template v-if="isImageUploadFile(file)">
          <img :src="file.url" class="upload-image" alt="" />
        </template>
        <template v-else>
          <div class="upload-doc">
            <el-icon class="doc-icon"><Document /></el-icon>
            <span class="doc-name" :title="file.name">{{ file.name || "文件" }}</span>
          </div>
        </template>
        <div class="upload-handle" @click.stop>
          <div class="handle-icon" @click="handlePreview(file)">
            <el-icon><ZoomIn /></el-icon>
            <span>查看</span>
          </div>
          <div v-if="!self_disabled" class="handle-icon" @click="handleRemove(file)">
            <el-icon><Delete /></el-icon>
            <span>删除</span>
          </div>
        </div>
      </template>
    </el-upload>
    <div class="el-upload__tip">
      <slot name="tip">
        <span>支持 JPG/PNG 图片与 PDF，单文件不超过 {{ fileSize }}MB，最多 {{ limit }} 个</span>
      </slot>
    </div>
    <el-image-viewer v-if="imgViewVisible" :url-list="[viewImageUrl]" @close="imgViewVisible = false" />
  </div>
</template>

<script setup lang="ts" name="UploadFiles">
import { ref, computed, inject, watch } from "vue";
import { Plus, Delete, ZoomIn, Document } from "@element-plus/icons-vue";
import { uploadImg } from "@/api/modules/upload";
import type { ReportFileItem } from "@/api/modules/bizCase";
import type { UploadProps, UploadFile, UploadUserFile, UploadRequestOptions } from "element-plus";
import { ElNotification, formContextKey, formItemContextKey } from "element-plus";

const IMAGE_MIME_SET = new Set(["image/jpeg", "image/png"]);
const PDF_MIME = "application/pdf";
const IMAGE_EXT_RE = /\.(jpe?g|png)$/i;
const PDF_EXT_RE = /\.pdf$/i;

interface UploadFilesProps {
  files: ReportFileItem[];
  api?: (params: FormData) => Promise<any>;
  drag?: boolean;
  disabled?: boolean;
  limit?: number;
  fileSize?: number;
  height?: string;
  width?: string;
  borderRadius?: string;
}

const props = withDefaults(defineProps<UploadFilesProps>(), {
  files: () => [],
  drag: true,
  disabled: false,
  limit: 10,
  fileSize: 10,
  height: "150px",
  width: "150px",
  borderRadius: "8px"
});

const accept = "image/jpeg,image/png,application/pdf,.jpg,.jpeg,.png,.pdf";

const emit = defineEmits<{
  "update:files": [value: ReportFileItem[]];
}>();

const formContext = inject(formContextKey, void 0);
const formItemContext = inject(formItemContextKey, void 0);

const self_disabled = computed(() => props.disabled || formContext?.disabled);

const _fileList = ref<UploadUserFile[]>([]);
/** uid -> mime，用于回写 v-model:files */
const mimeByUid = ref<Map<number | string, string>>(new Map());

const guessMime = (url: string, name?: string): string | undefined => {
  const target = (name || url).toLowerCase();
  if (PDF_EXT_RE.test(target)) return PDF_MIME;
  if (IMAGE_EXT_RE.test(target)) return "image/jpeg";
  return undefined;
};

const isImageItem = (item: { url?: string; name?: string; mime?: string }): boolean => {
  const mime = item.mime || guessMime(item.url || "", item.name);
  if (mime?.startsWith("image/")) return true;
  const target = `${item.url || ""} ${item.name || ""}`.toLowerCase();
  return IMAGE_EXT_RE.test(target);
};

const isImageUploadFile = (file: UploadFile): boolean => {
  const uid = file.uid;
  const mime = (uid != null ? mimeByUid.value.get(uid) : undefined) || guessMime(file.url || "", file.name);
  return mime ? mime.startsWith("image/") : isImageItem({ url: file.url, name: file.name });
};

const fileNameFromUrl = (url: string): string => {
  try {
    const path = new URL(url, window.location.origin).pathname;
    const base = path.split("/").pop() || "file";
    return decodeURIComponent(base);
  } catch {
    const parts = url.split("/");
    return parts[parts.length - 1] || "file";
  }
};

const reportFilesToUploadList = (files: ReportFileItem[]): UploadUserFile[] => {
  const map = new Map<number | string, string>();
  const list = files.map((item, index) => {
    const uid = `report-${index}-${item.url}`;
    const mime = item.mime || guessMime(item.url, item.name);
    if (mime) map.set(uid, mime);
    return {
      name: item.name || fileNameFromUrl(item.url),
      url: item.url,
      uid,
      status: "success" as const
    };
  });
  mimeByUid.value = map;
  return list;
};

const uploadListToReportFiles = (list: UploadUserFile[]): ReportFileItem[] => {
  return list
    .filter(f => f.status === "success" && f.url)
    .map(f => {
      const uid = f.uid;
      const mime = (uid != null ? mimeByUid.value.get(uid) : undefined) || guessMime(f.url!, f.name);
      return {
        url: f.url!,
        name: f.name,
        ...(mime ? { mime } : {})
      };
    });
};

const emitFiles = () => {
  emit("update:files", uploadListToReportFiles(_fileList.value));
  formItemContext?.prop && formContext?.validateField([formItemContext.prop as string]);
};

watch(
  () => props.files,
  (files: ReportFileItem[]) => {
    _fileList.value = reportFilesToUploadList(files || []);
  },
  { immediate: true, deep: true }
);

const isAllowedFile = (rawFile: File): boolean => {
  const type = rawFile.type;
  if (IMAGE_MIME_SET.has(type) || type === PDF_MIME) return true;
  const name = rawFile.name.toLowerCase();
  return IMAGE_EXT_RE.test(name) || PDF_EXT_RE.test(name);
};

const beforeUpload: UploadProps["beforeUpload"] = rawFile => {
  const okType = isAllowedFile(rawFile);
  const okSize = rawFile.size / 1024 / 1024 < props.fileSize;
  if (!okType) {
    ElNotification({
      title: "温馨提示",
      message: "仅支持 JPG、PNG 图片或 PDF 文件！",
      type: "warning"
    });
  }
  if (!okSize) {
    ElNotification({
      title: "温馨提示",
      message: `文件大小不能超过 ${props.fileSize}MB！`,
      type: "warning"
    });
  }
  return okType && okSize;
};

const handleHttpUpload = async (options: UploadRequestOptions) => {
  const formData = new FormData();
  formData.append("file", options.file);
  try {
    const api = props.api ?? uploadImg;
    const { data } = await api(formData);
    options.onSuccess(data);
  } catch (error) {
    options.onError(error as any);
  }
};

const uploadSuccess = (response: { fileUrl: string } | undefined, uploadFile: UploadFile) => {
  if (!response?.fileUrl) return;
  uploadFile.url = response.fileUrl;
  const raw = uploadFile.raw;
  const mime =
    raw?.type ||
    guessMime(response.fileUrl, uploadFile.name) ||
    (raw && isAllowedFile(raw) && PDF_EXT_RE.test(raw.name) ? PDF_MIME : "image/jpeg");
  if (uploadFile.uid != null && mime) {
    mimeByUid.value.set(uploadFile.uid, mime);
  }
  emitFiles();
  ElNotification({
    title: "温馨提示",
    message: "文件上传成功！",
    type: "success"
  });
};

const handleRemove = (file: UploadFile) => {
  _fileList.value = _fileList.value.filter(item => item.uid !== file.uid);
  if (file.uid != null) mimeByUid.value.delete(file.uid);
  emitFiles();
};

const uploadError = () => {
  ElNotification({
    title: "温馨提示",
    message: "文件上传失败，请您重新上传！",
    type: "error"
  });
};

const handleExceed = () => {
  ElNotification({
    title: "温馨提示",
    message: `当前最多只能上传 ${props.limit} 个文件，请移除后再上传！`,
    type: "warning"
  });
};

const viewImageUrl = ref("");
const imgViewVisible = ref(false);

const handlePreview = (file: UploadFile) => {
  const url = file.url;
  if (!url) return;
  if (isImageUploadFile(file)) {
    viewImageUrl.value = url;
    imgViewVisible.value = true;
    return;
  }
  window.open(url, "_blank", "noopener,noreferrer");
};
</script>

<style scoped lang="scss">
.is-error {
  .upload {
    :deep(.el-upload--picture-card),
    :deep(.el-upload-dragger) {
      border: 1px dashed var(--el-color-danger) !important;
      &:hover {
        border-color: var(--el-color-primary) !important;
      }
    }
  }
}
:deep(.disabled) {
  .el-upload--picture-card,
  .el-upload-dragger {
    cursor: not-allowed;
    background: var(--el-disabled-bg-color) !important;
    border: 1px dashed var(--el-border-color-darker);
    &:hover {
      border-color: var(--el-border-color-darker) !important;
    }
  }
}
.upload-box {
  .no-border {
    :deep(.el-upload--picture-card) {
      border: none !important;
    }
  }
  :deep(.upload) {
    .el-upload-dragger {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      padding: 0;
      overflow: hidden;
      border: 1px dashed var(--el-border-color-darker);
      border-radius: v-bind(borderRadius);
      &:hover {
        border: 1px dashed var(--el-color-primary);
      }
    }
    .el-upload-dragger.is-dragover {
      background-color: var(--el-color-primary-light-9);
      border: 2px dashed var(--el-color-primary) !important;
    }
    .el-upload-list__item,
    .el-upload--picture-card {
      width: v-bind(width);
      height: v-bind(height);
      background-color: transparent;
      border-radius: v-bind(borderRadius);
    }
    .upload-image {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    .upload-doc {
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      padding: 8px;
      text-align: center;
      .doc-icon {
        font-size: 36px;
        color: var(--el-color-danger);
      }
      .doc-name {
        display: -webkit-box;
        margin-top: 6px;
        overflow: hidden;
        font-size: 12px;
        line-height: 1.3;
        color: var(--el-text-color-regular);
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }
    }
    .upload-handle {
      position: absolute;
      top: 0;
      right: 0;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      cursor: pointer;
      background: rgb(0 0 0 / 60%);
      opacity: 0;
      transition: var(--el-transition-duration-fast);
      .handle-icon {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 0 6%;
        color: aliceblue;
        .el-icon {
          margin-bottom: 15%;
          font-size: 140%;
        }
        span {
          font-size: 100%;
        }
      }
    }
    .el-upload-list__item {
      &:hover {
        .upload-handle {
          opacity: 1;
        }
      }
    }
    .upload-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      font-size: 12px;
      line-height: 30px;
      color: var(--el-color-info);
      .el-icon {
        font-size: 28px;
        color: var(--el-text-color-secondary);
      }
    }
  }
  .el-upload__tip {
    line-height: 18px;
    color: var(--el-text-color-secondary);
  }
}
</style>
