<template>
  <div v-if="authStore.isSuperLogin" class="super-login-banner">
    <el-alert
      type="warning"
      :closable="false"
      show-icon
    >
      <template #title>
        <div class="banner-content">
          <span class="banner-text">
            ⚠️ 当前处于超级登录模式，正在以 
            <strong>{{ authStore.userInfo?.name }}</strong> 
            ({{ authStore.userInfo?.account }}) 的身份操作
          </span>
          <el-button
            type="primary"
            size="small"
            :loading="loading"
            @click="handleExitSuperLogin"
          >
            退出超级登录
          </el-button>
        </div>
      </template>
    </el-alert>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/modules/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const loading = ref(false)

/**
 * 退出超级登录
 */
const handleExitSuperLogin = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出超级登录吗？将恢复到原用户身份。',
      '退出超级登录',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    await authStore.exitSuperLogin()
    ElMessage.success('已退出超级登录')
    
    // 刷新页面
    router.go(0)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('退出超级登录失败:', error)
      ElMessage.error('退出超级登录失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.super-login-banner {
  position: sticky;
  top: 0;
  z-index: 1000;
  
  :deep(.el-alert) {
    border-radius: 0;
    margin: 0;
    padding: 12px 20px;
  }

  .banner-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;

    .banner-text {
      font-size: 14px;
      
      strong {
        color: #e6a23c;
        font-weight: 600;
      }
    }

    .el-button {
      margin-left: 20px;
    }
  }
}
</style>


