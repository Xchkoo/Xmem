<template>
  <div class="min-h-screen bg-primary text-gray-900">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="$emit('back')"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <div class="text-xl font-bold">记账统计</div>
      </div>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div v-if="loading" class="text-center py-12">
        <p class="text-gray-400">加载中...</p>
      </div>
      <div v-else-if="statistics" class="space-y-6">
        <!-- 月度小结卡片 -->
        <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
          <h2 class="text-lg font-bold text-gray-900 mb-4">月度小结</h2>
          
          <!-- 近6个月支出柱状图 -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-gray-600 mb-3">近6个月支出趋势</h3>
            <div class="h-64">
              <v-chart :option="monthlyChartOption" autoresize />
            </div>
          </div>

          <!-- 月度对比 -->
          <div v-if="statistics.current_month_total > 0 || statistics.last_month_total > 0" class="mt-6 p-4 bg-blue-50 rounded-xl">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600">本月 vs 上月</span>
              <span 
                class="text-sm font-semibold"
                :class="statistics.month_diff >= 0 ? 'text-red-600' : 'text-green-600'"
              >
                {{ statistics.month_diff >= 0 ? '+' : '' }}¥{{ Math.abs(statistics.month_diff).toLocaleString() }}
                ({{ statistics.month_diff_percent >= 0 ? '+' : '' }}{{ statistics.month_diff_percent.toFixed(1) }}%)
              </span>
            </div>
          </div>
        </div>

        <!-- 年度总结卡片 -->
        <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
          <h2 class="text-lg font-bold text-gray-900 mb-4">年度总结</h2>
          
          <!-- 每月支出柱状图 -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-gray-600 mb-3">全年支出趋势</h3>
            <div class="h-64">
              <v-chart :option="yearlyChartOption" autoresize />
            </div>
          </div>
        </div>

        <!-- 支出分类卡片 -->
        <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
          <h2 class="text-lg font-bold text-gray-900 mb-4">支出分类</h2>
          
          <!-- 分类占比饼图 -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-gray-600 mb-3">分类占比</h3>
            <div class="h-80">
              <v-chart :option="categoryChartOption" autoresize />
            </div>
          </div>

          <!-- 分类详情列表 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div 
              v-for="(item, index) in statistics.category_stats"
              :key="item.category"
              class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <div 
                class="w-4 h-4 rounded-full flex-shrink-0"
                :style="{ backgroundColor: getCategoryColor(index) }"
              ></div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm font-medium text-gray-900 truncate">{{ item.category }}</span>
                  <span class="text-sm font-semibold text-gray-700 ml-2">¥{{ item.amount.toLocaleString() }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      class="h-full transition-all duration-300"
                      :style="{ 
                        width: `${item.percentage}%`,
                        backgroundColor: getCategoryColor(index)
                      }"
                    ></div>
                  </div>
                  <span class="text-xs text-gray-500 w-12 text-right">{{ item.percentage.toFixed(1) }}%</span>
                </div>
                <div class="text-xs text-gray-500 mt-1">{{ item.count }} 笔</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-12">
        <p class="text-gray-400 text-lg">暂无统计数据</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart, PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
} from "echarts/components";
import VChart from "vue-echarts";
import type { LedgerStatistics } from "../stores/data";
import { useDataStore } from "../stores/data";

use([
  CanvasRenderer,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
]);

const emit = defineEmits<{
  back: [];
}>();

const data = useDataStore();
const statistics = ref<LedgerStatistics | null>(null);
const loading = ref(true);

// 月度图表配置
const monthlyChartOption = computed(() => {
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
      left: '10%',
      right: '10%',
      top: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: {
        fontSize: 12,
        color: '#6B7280'
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => `¥${(value / 1000).toFixed(0)}k`,
        fontSize: 12,
        color: '#6B7280'
      }
    },
    series: [
      {
        type: 'bar',
        data: amounts,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#3B82F6' },
              { offset: 1, color: '#60A5FA' }
            ]
          },
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

// 年度图表配置
const yearlyChartOption = computed(() => {
  if (!statistics.value || !statistics.value.yearly_data.length) {
    return undefined;
  }

  const months = statistics.value.yearly_data.map(item => {
    const [year, month] = item.month.split('-');
    return `${parseInt(month)}月`;
  });
  const amounts = statistics.value.yearly_data.map(item => item.amount);

  return {
    grid: {
      left: '10%',
      right: '10%',
      top: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: {
        fontSize: 11,
        color: '#6B7280',
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => `¥${(value / 1000).toFixed(0)}k`,
        fontSize: 12,
        color: '#6B7280'
      }
    },
    series: [
      {
        type: 'bar',
        data: amounts,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#8B5CF6' },
              { offset: 1, color: '#A78BFA' }
            ]
          },
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '50%'
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

// 分类饼图配置
const categoryChartOption = computed(() => {
  if (!statistics.value || !statistics.value.category_stats.length) {
    return undefined;
  }

  const colors = [
    '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981',
    '#EF4444', '#06B6D4', '#F97316', '#6366F1', '#14B8A6'
  ];

  const data = statistics.value.category_stats.map((item, index) => ({
    value: item.amount,
    name: item.category,
    itemStyle: {
      color: colors[index % colors.length]
    }
  }));

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.name}<br/>¥${params.value.toLocaleString()} (${params.percent}%)`;
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: data
      }
    ]
  };
});

// 获取分类颜色
const getCategoryColor = (index: number) => {
  const colors = [
    '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981',
    '#EF4444', '#06B6D4', '#F97316', '#6366F1', '#14B8A6'
  ];
  return colors[index % colors.length];
};

onMounted(async () => {
  loading.value = true;
  try {
    statistics.value = await data.fetchLedgerStatistics();
  } catch (error) {
    console.error("获取统计数据失败:", error);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.echarts {
  width: 100%;
  height: 100%;
}

.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}
</style>

