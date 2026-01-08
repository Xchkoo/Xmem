<template>
  <div 
    @click="$emit('click')"
    class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 cursor-pointer hover:shadow-lg transition-all duration-200 border border-blue-100"
  >
    <div class="flex items-center justify-between mb-3">
      <div>
        <h3 class="text-sm font-semibold text-gray-700">支出统计</h3>
        <p class="text-xs text-gray-500 mt-1">近6个月</p>
      </div>
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    </div>
    
    <!-- ECharts 图表 -->
    <div v-if="chartOption" class="h-24">
      <v-chart :option="chartOption" autoresize />
    </div>
    <div v-else class="h-24 flex items-center justify-center text-gray-400 text-sm">
      暂无数据
    </div>
    
    <div class="mt-3 flex items-center justify-between text-xs">
      <span class="text-gray-600">总支出: <span class="font-semibold text-gray-900">¥{{ totalAmount.toLocaleString() }}</span></span>
      <span class="text-blue-600 hover:text-blue-700">查看详情 →</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  GridComponent
} from "echarts/components";
import VChart from "vue-echarts";
import type { LedgerStatistics } from "../stores/data";
import { useDataStore } from "../stores/data";

use([
  CanvasRenderer,
  BarChart,
  TitleComponent,
  TooltipComponent,
  GridComponent
]);

const emit = defineEmits<{
  click: [];
}>();

const data = useDataStore();
const statistics = ref<LedgerStatistics | null>(null);

const chartOption = computed(() => {
  if (!statistics.value || !statistics.value.monthly_data.length) {
    return undefined;
  }

  const months = statistics.value.monthly_data.map(item => {
    const [year, month] = item.month.split('-');
    return `${parseInt(month)}月`;
  });
  const amounts = statistics.value.monthly_data.map(item => item.amount);

  return {
    grid: {
      left: '5%',
      right: '5%',
      top: '10%',
      bottom: '20%',
      containLabel: false
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: {
        fontSize: 10,
        color: '#6B7280'
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      show: false
    },
    series: [
      {
        type: 'bar',
        data: amounts,
        itemStyle: {
          color: '#3B82F6',
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '60%'
      }
    ],
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const param = params[0];
        return `${param.name}<br/>¥${param.value.toLocaleString()}`;
      }
    }
  };
});

const totalAmount = computed(() => {
  if (!statistics.value) return 0;
  return statistics.value.monthly_data.reduce((sum, item) => sum + item.amount, 0);
});

onMounted(async () => {
  try {
    statistics.value = await data.fetchLedgerStatistics();
  } catch (error) {
    console.error("获取统计数据失败:", error);
  }
});
</script>

<style scoped>
.echarts {
  width: 100%;
  height: 100%;
}
</style>

