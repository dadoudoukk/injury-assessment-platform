<template>
  <view class="container">
    <view class="header-section">
      <text class="page-title">我要报案</text>
      <text class="page-subtitle"
        >请如实填写案件信息，我们将为您就近分派鉴定机构</text
      >
    </view>

    <view class="form-section">
      <view class="input-group">
        <text class="label required">伤者姓名</text>
        <input
          v-model="form.victimName"
          class="input-field"
          placeholder="请输入伤者真实姓名"
          placeholder-class="ph-color"
        />
      </view>

      <view class="input-group">
        <text class="label required">联系电话</text>
        <input
          v-model="form.victimPhone"
          class="input-field"
          type="number"
          placeholder="请输入联系电话"
          placeholder-class="ph-color"
        />
      </view>

      <view class="input-group">
        <text class="label required">出险日期</text>
        <picker mode="date" :value="form.reportDate" @change="onDateChange">
          <view class="picker-field">
            <text :class="form.reportDate ? 'text-black' : 'ph-color'">
              {{ form.reportDate || "请选择出险日期" }}
            </text>
            <view class="arrow"></view>
          </view>
        </picker>
      </view>

      <view class="input-group">
        <text class="label required">出险地点</text>
        <picker mode="region" @change="onRegionChange">
          <view class="picker-field">
            <text :class="form.province ? 'text-black' : 'ph-color'">
              {{ form.province ? `${form.province} ${form.city} ${form.district}` : '请选择省/市/区' }}
            </text>
            <view class="arrow"></view>
          </view>
        </picker>
      </view>

      <view class="input-group">
        <text class="label required">事故类型</text>
        <picker
          :range="accidentTypeOptions"
          range-key="dictLabel"
          @change="onAccidentChange"
        >
          <view class="picker-field">
            <text :class="form.accidentType ? 'text-black' : 'ph-color'">
              {{
                getDictLabel(form.accidentType, accidentTypeOptions) ||
                "请选择事故类型"
              }}
            </text>
            <view class="arrow"></view>
          </view>
        </picker>
      </view>

      <view class="input-group">
        <text class="label required">伤情类型</text>
        <picker
          :range="injuryTypeOptions"
          range-key="dictLabel"
          @change="onInjuryChange"
        >
          <view class="picker-field">
            <text :class="form.injuryType ? 'text-black' : 'ph-color'">
              {{
                getDictLabel(form.injuryType, injuryTypeOptions) ||
                "请选择伤情类型"
              }}
            </text>
            <view class="arrow"></view>
          </view>
        </picker>
      </view>

      <view class="input-group">
        <text class="label required">出险报案号</text>
        <input
          v-model="form.reportNumber"
          class="input-field"
          placeholder="请输入保险出险报案号"
          placeholder-class="ph-color"
          maxlength="50"
        />
      </view>

      <view class="input-group">
        <text class="label required">承保保险公司</text>
        <input
          v-model="form.insuranceCompany"
          class="input-field"
          placeholder="请输入承保保险公司名称"
          placeholder-class="ph-color"
          maxlength="100"
        />
      </view>

      <button class="submit-btn" :loading="loading" @click="submitForm">
        提交报案
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { request } from "@/utils/request";

const loading = ref(false);

const form = reactive({
  victimName: "",
  victimPhone: "",
  reportDate: "",
  province: "",
  city: "",
  district: "",
  accidentType: "",
  injuryType: "",
  reportNumber: "",
  insuranceCompany: "",
});

const accidentTypeOptions = ref<any[]>([]);
const injuryTypeOptions = ref<any[]>([]);

const fetchDicts = async () => {
  try {
    const [accRes, injRes] = await Promise.all([
      request("/dict/data/biz_accident_type", "GET"),
      request("/dict/data/biz_injury_type", "GET"),
    ]);
    accidentTypeOptions.value = accRes || [];
    injuryTypeOptions.value = injRes || [];
  } catch (error) {
    console.error("Fetch dicts error:", error);
  }
};

onLoad(() => {
  fetchDicts();
});

const onDateChange = (e: any) => (form.reportDate = e.detail.value);
const onRegionChange = (e: any) => {
  const [province, city, district] = e.detail.value;
  form.province = province;
  form.city = city;
  form.district = district;
};
const onAccidentChange = (e: any) =>
  (form.accidentType = accidentTypeOptions.value[e.detail.value].dictValue);
const onInjuryChange = (e: any) =>
  (form.injuryType = injuryTypeOptions.value[e.detail.value].dictValue);

const getDictLabel = (val: string, options: any[]) => {
  const item = options.find((i) => i.dictValue === val);
  return item ? item.dictLabel : "";
};

const submitForm = async () => {
  if (
    !form.victimName ||
    !form.victimPhone ||
    !form.reportDate ||
    !form.province ||
    !form.city ||
    !form.district ||
    !form.accidentType ||
    !form.injuryType ||
    !form.reportNumber.trim() ||
    !form.insuranceCompany.trim()
  ) {
    return uni.showToast({ title: "请填写完整的必填项", icon: "none" });
  }

  loading.value = true;
  try {
    await request("/biz/case/patient", "POST", form);
    uni.showToast({ title: "报案成功！", icon: "success" });
    setTimeout(() => {
      uni.navigateBack();
      uni.$emit("refreshList");
    }, 1500);
  } catch (error) {
    console.error("Submit form error:", error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #ffffff;
  padding: 60rpx;
}

.header-section {
  margin-bottom: 80rpx;
}

.page-title {
  display: block;
  font-size: 48rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16rpx;
}

.page-subtitle {
  display: block;
  font-size: 28rpx;
  color: #6b7280;
}

.form-section {
  width: 100%;
}

.input-group {
  margin-bottom: 60rpx;
}

.label {
  display: block;
  font-size: 28rpx;
  color: #374151;
  font-weight: 500;
  margin-bottom: 20rpx;
}

.label.required::after {
  content: " *";
  color: #dc2626;
}

.input-field,
.picker-field {
  width: 100%;
  height: 80rpx;
  font-size: 32rpx;
  color: #111827;
  border-bottom: 2rpx solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s;
}

.input-field:focus {
  border-bottom-color: #111827;
}

.ph-color {
  color: #9ca3af;
  font-size: 30rpx;
}

.text-black {
  color: #111827;
}

.arrow {
  width: 16rpx;
  height: 16rpx;
  border-top: 4rpx solid #9ca3af;
  border-right: 4rpx solid #9ca3af;
  transform: rotate(45deg);
}

.submit-btn {
  margin-top: 80rpx;
  background-color: #2563eb;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 500;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 8rpx;
  letter-spacing: 2rpx;
}

.submit-btn::after {
  border: none;
}

.submit-btn:active {
  background-color: #1d4ed8;
}
</style>
