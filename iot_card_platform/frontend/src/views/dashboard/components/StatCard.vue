<template>
  <el-card class="stat-card" :body-style="{ padding: '20px' }">
    <div class="stat-content">
      <div class="stat-icon" :style="{ background: iconBg }">
        <el-icon :size="32" :color="iconColor">
          <component :is="icon" />
        </el-icon>
      </div>
      <div class="stat-info">
        <p class="stat-label">{{ label }}</p>
        <h3 class="stat-value">{{ value }}</h3>
        <p v-if="extra" class="stat-extra" :style="{ color: extraColor }">
          {{ extra }}
        </p>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

interface Props {
  label: string
  value: string | number
  icon: Component
  iconColor: string
  iconBg: string
  extra?: string
  extraColor?: string
}

defineProps<Props>()
</script>

<style scoped lang="scss">
.stat-card {
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .stat-content {
    display: flex;
    align-items: center;
    gap: 16px;

    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .stat-info {
      flex: 1;
      min-width: 0;

      .stat-label {
        font-size: 14px;
        color: #8c8c8c;
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: #262626;
        margin: 0;
      }

      .stat-extra {
        font-size: 12px;
        margin-top: 4px;
      }
    }
  }
}
</style>






