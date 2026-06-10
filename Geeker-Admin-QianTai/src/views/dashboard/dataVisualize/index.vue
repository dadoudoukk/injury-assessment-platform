<template>
  <div class="dataVisualize-box">
    <div class="card top-box">
      <div class="top-title">案件统计大盘</div>
      <el-tabs v-model="tabActive" class="demo-tabs" style="display: none">
        <el-tab-pane v-for="item in tab" :key="item.name" :label="item.label" :name="item.name"></el-tab-pane>
      </el-tabs>
      <div class="top-content">
        <el-row :gutter="40">
          <el-col class="mb40" :xs="24" :sm="12" :md="12" :lg="6" :xl="6">
            <div class="item-left sle">
              <span class="left-title">案件总数</span>
              <div class="img-box">
                <img src="./images/book-sum.png" alt="" />
              </div>
              <span class="left-number">{{ statsData.total || 0 }}</span>
            </div>
          </el-col>
          <el-col class="mb40" :xs="24" :sm="12" :md="12" :lg="8" :xl="8">
            <div class="item-center">
              <div class="gitee-traffic traffic-box">
                <div class="traffic-img">
                  <img src="./images/add_person.png" alt="" />
                </div>
                <span class="item-value">{{ statsData.pending || 0 }}</span>
                <span class="traffic-name sle">待接单案件</span>
              </div>
              <div class="gitHub-traffic traffic-box">
                <div class="traffic-img">
                  <img src="./images/add_team.png" alt="" />
                </div>
                <span class="item-value">{{ statsData.inProgress || 0 }}</span>
                <span class="traffic-name sle">鉴定中案件</span>
              </div>
              <div class="today-traffic traffic-box">
                <div class="traffic-img">
                  <img src="./images/today.png" alt="" />
                </div>
                <span class="item-value">{{ statsData.completed || 0 }}</span>
                <span class="traffic-name sle">已完成案件</span>
              </div>
              <div class="yesterday-traffic traffic-box">
                <div class="traffic-img">
                  <img src="./images/book_sum.png" alt="" />
                </div>
                <span class="item-value">{{ ((statsData.completed / (statsData.total || 1)) * 100).toFixed(1) }}%</span>
                <span class="traffic-name sle">结案率</span>
              </div>
            </div>
          </el-col>
          <el-col class="mb40" :xs="24" :sm="24" :md="24" :lg="10" :xl="10">
            <div class="item-right">
              <div class="echarts-title">各保险公司案件占比</div>
              <div class="book-echarts">
                <Pie ref="pieRef" :pie-data="statsData.insuranceStats" />
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>
    <div class="card bottom-box">
      <div class="bottom-title">近两周报案趋势</div>
      <div class="bottom-tabs">
        <el-tabs v-model="tabActive" class="demo-tabs" style="display: none">
          <el-tab-pane v-for="item in tab" :key="item.name" :label="item.label" :name="item.name"></el-tab-pane>
        </el-tabs>
      </div>
      <div class="curve-echarts">
        <Curve ref="curveRef" :curve-data="statsData.trendStats" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="dataVisualize">
import { ref, onMounted } from "vue";
import Pie from "./components/pie.vue";
import Curve from "./components/curve.vue";
import { getCaseStats } from "@/api/modules/bizCase";

const tabActive = ref(1);
const statsData = ref<any>({
  total: 0,
  pending: 0,
  inProgress: 0,
  completed: 0,
  insuranceStats: [],
  trendStats: []
});

const tab = [{ label: "未来7日", name: 1 }];

onMounted(async () => {
  try {
    const res = await getCaseStats();
    if (res && res.data) {
      statsData.value = res.data;
    }
  } catch (error) {
    console.error("Failed to fetch stats", error);
  }
});
</script>

<style scoped lang="scss">
@import "./index.scss";
</style>
