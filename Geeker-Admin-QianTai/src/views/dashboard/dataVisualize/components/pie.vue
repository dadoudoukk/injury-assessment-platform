<template>
  <div class="echarts">
    <ECharts :option="option" />
  </div>
</template>

<script setup lang="ts" name="pie">
import { computed } from "vue";
import { ECOption } from "@/components/ECharts/config";
import ECharts from "@/components/ECharts/index.vue";

const props = defineProps<{
  pieData: Array<{ name: string; value: number }>;
}>();

const option = computed<ECOption>(() => {
  const data = props.pieData && props.pieData.length ? props.pieData : [{ name: "暂无数据", value: 0 }];

  return {
    title: {
      text: "保险公司",
      subtext: "案件占比",
      left: "56%",
      top: "45%",
      textAlign: "center",
      textStyle: {
        fontSize: 18,
        color: "#767676"
      },
      subtextStyle: {
        fontSize: 15,
        color: "#a1a1a1"
      }
    },
    tooltip: {
      trigger: "item"
    },
    legend: {
      top: "4%",
      left: "2%",
      orient: "vertical",
      icon: "circle",
      align: "left",
      itemGap: 20,
      textStyle: {
        fontSize: 13,
        color: "#a1a1a1",
        fontWeight: 500
      },
      formatter: function (name: string) {
        let dataCopy = "";
        for (let i = 0; i < data.length; i++) {
          if (data[i].name == name && data[i].value >= 10000) {
            dataCopy = (data[i].value / 10000).toFixed(2);
            return name + "      " + dataCopy + "w";
          } else if (data[i].name == name) {
            dataCopy = data[i].value + "";
            return name + "      " + dataCopy;
          }
        }
        return name;
      }
    },
    series: [
      {
        type: "pie",
        radius: ["70%", "40%"],
        center: ["57%", "52%"],
        silent: false,
        clockwise: true,
        startAngle: 150,
        data: data,
        labelLine: {
          length: 80,
          length2: 30,
          lineStyle: {
            width: 1
          }
        },
        label: {
          position: "outside",
          show: true,
          formatter: "{d}%",
          fontWeight: 400,
          fontSize: 19,
          color: "#a1a1a1"
        },
        color: ["#feb791", "#b898fd", "#8347fd", "#3cba92", "#0ba360", "#f59a23", "#1890ff", "#ff4d4f"]
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
