<template>
  <div class="system-container">
    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="个人中心" name="profile">
          <ProfilePanel />
        </el-tab-pane>
        <el-tab-pane label="系统配置" name="config">
          <ConfigPanel />
        </el-tab-pane>
        <el-tab-pane label="告警规则" name="alert">
          <AlertRulesPanel />
        </el-tab-pane>
        <el-tab-pane label="登录日志" name="loginLog">
          <LoginLogPanel />
        </el-tab-pane>
        <el-tab-pane label="操作日志" name="operationLog">
          <OperationLogPanel />
        </el-tab-pane>
        <el-tab-pane label="通知模板" name="notify">
          <NotifyTemplatePanel />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ProfilePanel from './components/ProfilePanel.vue'
import ConfigPanel from './components/ConfigPanel.vue'
import AlertRulesPanel from './components/AlertRulesPanel.vue'
import LoginLogPanel from './components/LoginLogPanel.vue'
import OperationLogPanel from './components/OperationLogPanel.vue'
import NotifyTemplatePanel from './components/NotifyTemplatePanel.vue'

const route = useRoute()
const activeTab = ref(route.query.tab as string || 'profile')
</script>

<style scoped lang="scss">
.system-container {
  padding: 20px;
}
</style>
