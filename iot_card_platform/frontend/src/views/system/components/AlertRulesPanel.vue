<template>
  <div class="alert-rules-panel">
    <el-form
      v-loading="loading"
      ref="formRef"
      :model="form"
      label-width="140px"
      style="max-width: 600px"
    >
      <el-form-item label="警告阈值 (%)">
        <el-input-number
          v-model="form.warning_threshold"
          :min="0"
          :max="100"
          style="width: 200px"
        />
        <span class="form-tip">流量使用达到此百分比时发出警告</span>
      </el-form-item>
      <el-form-item label="紧急阈值 (%)">
        <el-input-number
          v-model="form.critical_threshold"
          :min="0"
          :max="100"
          style="width: 200px"
        />
        <span class="form-tip">流量使用达到此百分比时发出紧急告警</span>
      </el-form-item>
      <el-form-item label="停卡阈值 (%)">
        <el-input-number
          v-model="form.stop_threshold"
          :min="0"
          :max="100"
          style="width: 200px"
        />
        <span class="form-tip">流量使用达到此百分比时自动停卡</span>
      </el-form-item>
      <el-form-item label="到期预警天数">
        <el-input-number
          v-model="form.expired_days"
          :min="1"
          :max="30"
          style="width: 200px"
        />
        <span class="form-tip">卡片到期前多少天发出预警</span>
      </el-form-item>
      <el-form-item label="告警自动通知">
        <el-switch v-model="form.auto_notify" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSave">
          保存设置
        </el-button>
        <el-button @click="fetchRules">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi } from '@/api/modules/system'

const loading = ref(false)
const saving = ref(false)

const form = reactive({
  warning_threshold: 80,
  critical_threshold: 90,
  stop_threshold: 100,
  expired_days: 7,
  auto_suspend: true,
  auto_notify: true
})

const fetchRules = async () => {
  loading.value = true
  try {
    const data = await systemApi.getAlertRules()
    if (data) {
      form.warning_threshold = data.warning_threshold ?? 80
      form.critical_threshold = data.critical_threshold ?? 90
      form.stop_threshold = data.stop_threshold ?? 100
      form.expired_days = data.expired_days ?? 7
      form.auto_suspend = data.auto_suspend ?? true
      form.auto_notify = data.auto_notify ?? true
    }
  } catch (error) {
    console.error('获取告警规则失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await systemApi.updateAlertRules({ ...form })
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存告警规则失败:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchRules()
})
</script>

<style scoped lang="scss">
.alert-rules-panel {
  padding: 16px 0;

  .form-tip {
    margin-left: 12px;
    color: #909399;
    font-size: 12px;
  }
}
</style>
