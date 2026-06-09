<template>
  <view class="container">
    <view class="header-banner">
      <view class="title">我要报案</view>
      <view class="subtitle">请如实填写案件信息，我们将为您就近分派鉴定机构</view>
    </view>

    <view class="form-card">
      <view class="form-item">
        <text class="form-label required">伤者姓名</text>
        <input v-model="form.victimName" class="form-input" placeholder="请输入伤者真实姓名" />
      </view>

      <view class="form-item">
        <text class="form-label required">联系电话</text>
        <input v-model="form.victimPhone" class="form-input" type="number" placeholder="请输入联系电话" />
      </view>

      <view class="form-item">
        <text class="form-label required">出险日期</text>
        <picker mode="date" :value="form.reportDate" @change="onDateChange">
          <view class="form-picker" :class="form.reportDate ? '' : 'placeholder'">
            {{ form.reportDate || '请选择出险日期' }}
          </view>
        </picker>
      </view>

      <view class="form-item">
        <text class="form-label required">出险地点（省）</text>
        <input v-model="form.province" class="form-input" placeholder="例如：浙江省" />
      </view>
      <view class="form-item">
        <text class="form-label required">出险地点（市）</text>
        <input v-model="form.city" class="form-input" placeholder="例如：杭州市" />
      </view>
      <view class="form-item">
        <text class="form-label required">出险地点（区/县）</text>
        <input v-model="form.district" class="form-input" placeholder="例如：西湖区" />
      </view>

      <view class="form-item">
        <text class="form-label required">事故类型</text>
        <picker :range="accidentTypeOptions" range-key="dictLabel" @change="onAccidentChange">
          <view class="form-picker" :class="form.accidentType ? '' : 'placeholder'">
            {{ getDictLabel(form.accidentType, accidentTypeOptions) || '请选择事故类型' }}
          </view>
        </picker>
      </view>

      <view class="form-item">
        <text class="form-label required">伤情类型</text>
        <picker :range="injuryTypeOptions" range-key="dictLabel" @change="onInjuryChange">
          <view class="form-picker" :class="form.injuryType ? '' : 'placeholder'">
            {{ getDictLabel(form.injuryType, injuryTypeOptions) || '请选择伤情类型' }}
          </view>
        </picker>
      </view>

      <view class="form-item">
        <text class="form-label required">承保保险公司</text>
        <picker :range="insuranceCompanyOptions" range-key="dictLabel" @change="onInsuranceChange">
          <view class="form-picker" :class="form.insuranceCompany ? '' : 'placeholder'">
             {{ getDictLabel(form.insuranceCompany, insuranceCompanyOptions) || '请选择保险公司' }}
          </view>
        </picker>
      </view>

      <button class="submit-btn" :loading="loading" @click="submitForm">提交报案</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { request } from '@/utils/request'

const loading = ref(false)

const form = reactive({
  victimName: '',
  victimPhone: '',
  reportDate: '',
  province: '',
  city: '',
  district: '',
  accidentType: '',
  injuryType: '',
  insuranceCompany: ''
})

const accidentTypeOptions = ref<any[]>([])
const injuryTypeOptions = ref<any[]>([])
const insuranceCompanyOptions = ref<any[]>([])

const fetchDicts = async () => {
  try {
    const [accRes, injRes, insRes] = await Promise.all([
      request('/dict/data/type/biz_accident_type', 'GET'),
      request('/dict/data/type/biz_injury_type', 'GET'),
      request('/biz/insurance/all', 'GET')
    ])
    accidentTypeOptions.value = accRes || []
    injuryTypeOptions.value = injRes || []
    insuranceCompanyOptions.value = (insRes || []).map((item: any) => ({
      dictLabel: item.companyName,
      dictValue: item.companyName
    }))
  } catch (error) {
    console.error('Fetch dicts error:', error)
  }
}

onLoad(() => {
  fetchDicts()
})

const onDateChange = (e: any) => form.reportDate = e.detail.value
const onAccidentChange = (e: any) => form.accidentType = accidentTypeOptions.value[e.detail.value].dictValue
const onInjuryChange = (e: any) => form.injuryType = injuryTypeOptions.value[e.detail.value].dictValue
const onInsuranceChange = (e: any) => form.insuranceCompany = insuranceCompanyOptions.value[e.detail.value].dictValue

const getDictLabel = (val: string, options: any[]) => {
  const item = options.find(i => i.dictValue === val)
  return item ? item.dictLabel : ''
}

const submitForm = async () => {
  if (!form.victimName || !form.victimPhone || !form.reportDate || !form.province || !form.city || !form.district || !form.accidentType || !form.injuryType || !form.insuranceCompany) {
    return uni.showToast({ title: '请填写完整的必填项', icon: 'none' })
  }

  loading.value = true
  try {
    await request('/biz/case/patient', 'POST', form)
    uni.showToast({ title: '报案成功！', icon: 'success' })
    setTimeout(() => {
      // 成功后跳回列表页或刷新列表
      uni.navigateBack()
      // 或者触发上个页面的刷新事件
      uni.$emit('refreshList')
    }, 1500)
  } catch (error) {
    console.error('Submit form error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f4f7f6;
  padding-bottom: 60rpx;
}
.header-banner {
  background: linear-gradient(135deg, #0ba360 0%, #3cba92 100%);
  padding: 60rpx 40rpx 80rpx;
  color: #fff;
}
.title {
  font-size: 44rpx;
  font-weight: bold;
}
.subtitle {
  font-size: 26rpx;
  margin-top: 16rpx;
  opacity: 0.9;
}
.form-card {
  background-color: #fff;
  border-radius: 24rpx;
  margin: -40rpx 30rpx 0;
  padding: 40rpx 30rpx;
  box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.05);
  position: relative;
  z-index: 10;
}
.form-item {
  margin-bottom: 30rpx;
}
.form-label {
  display: block;
  font-size: 28rpx;
  color: #333;
  margin-bottom: 16rpx;
}
.form-label.required::after {
  content: '*';
  color: #f5222d;
  margin-left: 8rpx;
}
.form-input, .form-picker {
  background-color: #f8f9fa;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #333;
}
.form-picker.placeholder {
  color: #999;
}
.submit-btn {
  background: linear-gradient(90deg, #0ba360 0%, #3cba92 100%);
  color: #ffffff;
  border-radius: 50rpx;
  font-size: 32rpx;
  margin-top: 60rpx;
}
</style>
