<template>
  <div class="suspend-logs-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>停卡记录</span>
        </div>
      </template>

      <el-empty description="停卡记录页待接入，当前请先在卡片详情和系统日志中查看相关记录" />
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.suspend-logs-container {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
