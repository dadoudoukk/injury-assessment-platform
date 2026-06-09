<template>
  <div class="echarts">
    <ECharts :option="option" />
  </div>
</template>

<script setup lang="ts" name="curve">
import { computed } from "vue";
import { ECOption } from "@/components/ECharts/config";
import ECharts from "@/components/ECharts/index.vue";

const props = defineProps<{
  curveData: Array<{ date: string; count: number }>;
}>();

const option = computed<ECOption>(() => {
  const data = props.curveData && props.curveData.length ? props.curveData : [];
  
  return {
    tooltip: {
      trigger: "axis",
      backgroundColor: "transparent",
      axisPointer: {
        type: "none"
      },
      padding: 0,
      formatter: (p: any) => {
        let dom = `<div style="width:100%; height: 70px !important; display:flex;flex-direction: column;justify-content: space-between;padding:10px;box-sizing: border-box;
        color:#fff; background: #6B9DFE;border-radius: 4px;font-size:14px; ">
          <div style="display: flex; align-items: center;"> <div style="width:5px;height:5px;background:#ffffff;border-radius: 50%;margin-right:5px"></div>日期 :  ${p[0].name}</div>
          <div style="display: flex;align-items: center;"><div style="width:5px;height:5px;background:#ffffff;border-radius: 50%;margin-right:5px"></div>报案量 :  ${p[0].value}</div>
        </div>`;
        return dom;
      }
    },
    toolbox: {
      show: true,
      orient: "horizontal"
    },
    grid: {
      left: "0",
      right: "0"
    },
    dataZoom: [
      {
        show: false,
        height: 10,
        xAxisIndex: [0],
        bottom: 0,
        startValue: 0,
        endValue: 9,
        handleStyle: {
          color: "#6b9dfe"
        },
        textStyle: {
          color: "transparent"
        }
      },
      {
        type: "inside",
        show: true,
        height: 0,
        zoomLock: true
      }
    ],
    xAxis: [
      {
        type: "category",
        data: data.map((val: any) => {
          return {
            value: val.date
          };
        }),
        axisTick: {
          show: false
        },
        axisLabel: {
          margin: 20,
          interval: 0,
          color: "#a1a1a1",
          fontSize: 14,
          formatter: function (name: string) {
            return name.length > 8 ? name.slice(5) : name; // 显示月-日
          }
        },
        axisLine: {
          lineStyle: {
            color: "#c0c0c0"
          }
        }
      }
    ],
    yAxis: [
      {
        min: 0,
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: "#c0c0c0"
          }
        },
        axisLabel: {
          color: "#a1a1a1",
          fontSize: 16,
          fontWeight: 400,
          formatter: function (value: number) {
            if (value === 0) {
              return value + "";
            } else if (value >= 10000) {
              return value / 10000 + "w";
            }
            return value + "";
          }
        }
      }
    ],
    series: [
      {
        name: "Direct",
        type: "bar",
        data: data.map((val: any) => {
          return {
            value: val.count
          };
        }),
        barWidth: "45px",
        itemStyle: {
          color: "#C5D8FF",
          borderRadius: [12, 12, 0, 0]
        },
        emphasis: {
          itemStyle: {
            color: "#6B9DFE"
          }
        }
      }
    ]
  };
});
</script>

<style lang="scss" scoped>
.echarts {
  width: 100%;
  height: 100%;
}
</style>
