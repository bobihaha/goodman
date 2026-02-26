<template>
  <el-card 
    class="stat-card" 
    :class="{ 'is-clickable': clickable }"
    :body-style="{ padding: '14px 16px' }"
    @click="handleClick"
  >
    <div class="stat-content">
      <div class="stat-icon" :style="{ background: iconBg }">
        <el-icon :size="24" :color="iconColor">
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
  clickable?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'click'): void
}>()

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style scoped lang="scss">
.stat-card {
  transition: all 0.3s;

  &.is-clickable {
    cursor: pointer;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    }
  }

  .stat-content {
    display: flex;
    align-items: center;
    gap: 12px;

    .stat-icon {
      width: 44px;
      height: 44px;
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
        font-size: 13px;
        color: #8c8c8c;
        margin-bottom: 4px;
      }

      .stat-value {
        font-size: 20px;
        font-weight: 600;
        color: #262626;
        margin: 0;
      }

      .stat-extra {
        font-size: 12px;
        margin-top: 2px;
      }
    }
  }
}
</style>
