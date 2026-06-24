<template>
  <div class="home-container" v-loading="loading">
    <!-- 顶部数据看板 -->
    <el-row :gutter="20" class="panel-group">
      <el-col :xs="24" :sm="12" :lg="6" v-for="(item, index) in panelData" :key="index">
        <el-card shadow="hover" class="panel-card">
          <div class="panel-header">
            <span class="panel-title">{{ item.title }}</span>
            <el-tag :type="item.tagType" effect="light" size="small" v-if="item.tag">{{ item.tag }}</el-tag>
          </div>
          <div class="panel-content">
            <div class="panel-number">{{ item.value }}</div>
            <el-icon class="panel-icon" :style="{ color: item.color }"><component :is="item.icon" /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 待办提醒卡片 -->
    <el-row v-if="todoItems.length" :gutter="16" class="todo-group">
      <el-col :span="24">
        <el-card shadow="hover" class="todo-section-card">
          <template #header>
            <div class="card-header">
              <span>我的待办</span>
              <el-badge :value="todoTotal" :max="99" type="danger" />
            </div>
          </template>
          <el-row :gutter="16">
            <el-col v-for="item in todoItems" :key="item.key" :xs="24" :sm="12" :lg="6">
              <div class="home-todo-card" @click="goTodo(item)">
                <div class="home-todo-card__head">
                  <span class="home-todo-card__title">{{ item.title }}</span>
                  <el-tag type="danger" size="small">{{ item.count }}</el-tag>
                </div>
                <p class="home-todo-card__desc">{{ item.description }}</p>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 中部可视化图表 -->
    <el-row :gutter="20" class="chart-group">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>近30天案件新增趋势</span>
            </div>
          </template>
          <div ref="lineChartRef" class="chart-content"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>案件当前状态占比</span>
            </div>
          </template>
          <div ref="pieChartRef" class="chart-content"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部动态列表 -->
    <el-row class="timeline-group">
      <el-col :span="24">
        <el-card shadow="hover" class="timeline-card">
          <template #header>
            <div class="card-header">
              <span>最新案件流转动态</span>
            </div>
          </template>
          <el-empty v-if="!activities.length" description="暂无案件流转记录" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="(activity, index) in activities"
              :key="index"
              :type="activity.type"
              :color="activity.color"
              :size="activity.size"
              :timestamp="activity.timestamp"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts" name="home">
import { ref, onMounted, onBeforeUnmount, shallowRef, markRaw } from "vue";
import { useRouter } from "vue-router";
import { DataLine, Warning, OfficeBuilding, Money } from "@element-plus/icons-vue";
import * as echarts from "echarts";
import { getCaseStats, type CaseRecentActivity, type CaseStatsData } from "@/api/modules/bizCase";
import { getWorkbenchTodos, type WorkbenchTodoItem } from "@/api/modules/bizHome";

const router = useRouter();

interface PanelData {
  title: string;
  value: string;
  tag: string;
  tagType: "success" | "warning" | "info" | "primary" | "danger" | undefined;
  icon: any;
  color: string;
}

interface Activity extends CaseRecentActivity {
  size?: "large" | "normal";
  color?: string;
}

const loading = ref(false);
const todoItems = ref<WorkbenchTodoItem[]>([]);
const todoTotal = ref(0);
const panelData = ref<PanelData[]>([
  {
    title: "累计案件总数",
    value: "0",
    tag: "",
    tagType: "info",
    icon: markRaw(DataLine),
    color: "var(--el-color-primary)"
  },
  {
    title: "待派发/待受理案件",
    value: "0",
    tag: "",
    tagType: "info",
    icon: markRaw(Warning),
    color: "var(--el-color-warning)"
  },
  {
    title: "入驻鉴定机构",
    value: "0",
    tag: "",
    tagType: "info",
    icon: markRaw(OfficeBuilding),
    color: "var(--el-color-success)"
  },
  {
    title: "合作保险公司",
    value: "0",
    tag: "",
    tagType: "info",
    icon: markRaw(Money),
    color: "var(--el-color-danger)"
  }
]);

const activities = ref<Activity[]>([]);

const lineChartRef = ref<HTMLElement | null>(null);
const pieChartRef = ref<HTMLElement | null>(null);
const lineChart = shallowRef<echarts.ECharts | null>(null);
const pieChart = shallowRef<echarts.ECharts | null>(null);

const formatNumber = (value?: number) => (value ?? 0).toLocaleString("zh-CN");

const formatWeekGrowthTag = (growth?: number) => {
  const rate = growth ?? 0;
  if (rate > 0) return { tag: `+${rate}% 周环比`, tagType: "success" as const };
  if (rate < 0) return { tag: `${rate}% 周环比`, tagType: "danger" as const };
  return { tag: "周环比持平", tagType: "info" as const };
};

/** 兼容旧版/不完整 stats 响应，避免缺字段导致页面渲染中断 */
const normalizeStats = (raw: CaseStatsData): Required<CaseStatsData> => {
  const pending = raw.pending ?? 0;
  const inProgress = raw.inProgress ?? 0;
  const completed = raw.completed ?? 0;
  const rework = raw.rework ?? 0;
  const statusStats =
    raw.statusStats?.length && raw.statusStats.some(item => item.value > 0)
      ? raw.statusStats
      : [
          { name: "待确认", value: pending },
          { name: "鉴定中", value: inProgress },
          { name: "已完成", value: completed },
          { name: "已打回", value: rework }
        ].filter(item => item.value > 0);

  return {
    total: raw.total ?? 0,
    pending,
    inProgress,
    completed,
    rework,
    agencyCount: raw.agencyCount ?? 0,
    insuranceCount: raw.insuranceCount ?? 0,
    weekGrowth: raw.weekGrowth ?? 0,
    statusStats,
    insuranceStats: raw.insuranceStats ?? [],
    trendStats: raw.trendStats ?? [],
    recentActivities: raw.recentActivities ?? []
  };
};

const buildPanelData = (stats: Required<CaseStatsData>) => {
  const weekGrowthTag = formatWeekGrowthTag(stats.weekGrowth);
  panelData.value = [
    {
      title: "累计案件总数",
      value: formatNumber(stats.total),
      tag: weekGrowthTag.tag,
      tagType: weekGrowthTag.tagType,
      icon: markRaw(DataLine),
      color: "var(--el-color-primary)"
    },
    {
      title: "待派发/待受理案件",
      value: formatNumber(stats.pending),
      tag: stats.pending > 0 ? "需及时处理" : "暂无积压",
      tagType: stats.pending > 0 ? "danger" : "success",
      icon: markRaw(Warning),
      color: "var(--el-color-warning)"
    },
    {
      title: "入驻鉴定机构",
      value: formatNumber(stats.agencyCount),
      tag: stats.agencyCount > 0 ? "已入驻" : "待拓展",
      tagType: "info",
      icon: markRaw(OfficeBuilding),
      color: "var(--el-color-success)"
    },
    {
      title: "合作保险公司",
      value: formatNumber(stats.insuranceCount),
      tag: stats.insuranceCount > 0 ? "合作中" : "待拓展",
      tagType: "info",
      icon: markRaw(Money),
      color: "var(--el-color-danger)"
    }
  ];
};

const updateLineChart = (trendStats: CaseStatsData["trendStats"]) => {
  if (!lineChartRef.value) return;
  if (!lineChart.value) lineChart.value = echarts.init(lineChartRef.value);

  const dates = trendStats.map(item => item.date);
  const counts = trendStats.map(item => item.count);

  lineChart.value.setOption({
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: "value",
      minInterval: 1
    },
    series: [
      {
        name: "新增案件",
        type: "line",
        smooth: true,
        itemStyle: { color: "#409eff" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(64,158,255,0.3)" },
            { offset: 1, color: "rgba(64,158,255,0.05)" }
          ])
        },
        data: counts
      }
    ]
  });
};

const updatePieChart = (statusStats: CaseStatsData["statusStats"]) => {
  if (!pieChartRef.value) return;
  if (!pieChart.value) pieChart.value = echarts.init(pieChartRef.value);

  pieChart.value.setOption({
    tooltip: { trigger: "item" },
    legend: { top: "5%", left: "center" },
    series: [
      {
        name: "案件状态",
        type: "pie",
        radius: ["40%", "70%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: "#fff",
          borderWidth: 2
        },
        label: { show: false, position: "center" },
        emphasis: {
          label: { show: true, fontSize: "20", fontWeight: "bold" }
        },
        labelLine: { show: false },
        data: statusStats
      }
    ]
  });
};

const buildActivities = (recentActivities: CaseRecentActivity[]) => {
  activities.value = recentActivities.map((item, index) => ({
    ...item,
    size: index < 2 ? "large" : "normal"
  }));
};

const fetchDashboardData = async () => {
  loading.value = true;
  try {
    const res = await getCaseStats();
    if (!res?.data) return;

    const stats = normalizeStats(res.data);
    buildPanelData(stats);
    buildActivities(stats.recentActivities);
    updateLineChart(stats.trendStats);
    updatePieChart(stats.statusStats);
  } catch (error) {
    console.error("获取首页统计数据失败", error);
  } finally {
    loading.value = false;
  }
};

const fetchTodos = async () => {
  try {
    const res = await getWorkbenchTodos();
    todoItems.value = res.data?.items || [];
    todoTotal.value = res.data?.total || 0;
  } catch (error) {
    console.error("获取首页待办失败", error);
  }
};

const goTodo = (item: WorkbenchTodoItem) => {
  router.push({
    path: item.path,
    query: item.query || {}
  });
};

const resizeChart = () => {
  lineChart.value?.resize();
  pieChart.value?.resize();
};

onMounted(async () => {
  await Promise.all([fetchDashboardData(), fetchTodos()]);
  window.addEventListener("resize", resizeChart);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeChart);
  lineChart.value?.dispose();
  pieChart.value?.dispose();
});
</script>

<style scoped lang="scss">
.home-container {
  width: 100%;
  height: 100%;
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  background-color: transparent;

  .panel-group {
    margin-bottom: 20px;

    .panel-card {
      margin-bottom: 20px;
      border-radius: 8px;
      border: none;

      .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 15px;

        .panel-title {
          font-size: 14px;
          color: var(--el-text-color-secondary);
        }
      }

      .panel-content {
        display: flex;
        align-items: center;
        justify-content: space-between;

        .panel-number {
          font-size: 28px;
          font-weight: bold;
          color: var(--el-text-color-primary);
        }

        .panel-icon {
          font-size: 48px;
          opacity: 0.8;
        }
      }
    }
  }

  .todo-group {
    margin-bottom: 20px;

    .todo-section-card {
      border-radius: 8px;
      border: none;

      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 16px;
        font-weight: bold;
      }
    }

    .home-todo-card {
      margin-bottom: 12px;
      padding: 14px 16px;
      border: 1px solid var(--el-border-color-lighter);
      border-radius: 8px;
      cursor: pointer;
      transition:
        border-color 0.15s ease,
        box-shadow 0.15s ease;

      &:hover {
        border-color: var(--el-color-primary-light-5);
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.12);
      }

      &__head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
      }

      &__title {
        font-size: 15px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      &__desc {
        margin: 0;
        font-size: 13px;
        color: var(--el-text-color-secondary);
        line-height: 1.5;
      }
    }
  }

  .chart-group {
    margin-bottom: 20px;

    .chart-card {
      margin-bottom: 20px;
      border-radius: 8px;
      border: none;

      .card-header {
        font-size: 16px;
        font-weight: bold;
      }

      .chart-content {
        height: 350px;
        width: 100%;
      }
    }
  }

  .timeline-group {
    .timeline-card {
      border-radius: 8px;
      border: none;

      .card-header {
        font-size: 16px;
        font-weight: bold;
      }

      :deep(.el-timeline) {
        padding-top: 10px;
        padding-left: 10px;
      }
    }
  }
}
</style>
