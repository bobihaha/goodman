<template>
  <div class="h5-page">
    <div class="hero" :style="heroStyle">
      <div class="hero__overlay" />
      <div class="hero__content">
        <img v-if="config?.logo" :src="config.logo" alt="logo" class="hero__logo" />
        <div class="hero__title">{{ config?.title || '卡片自助服务' }}</div>
        <div class="hero__subtitle">输入卡号、ICCID、移动后6位，或联通电信后2-7位即可查询</div>
      </div>
    </div>

    <div class="content">
      <el-alert
        v-if="config?.notice"
        :title="config.notice"
        type="info"
        :closable="false"
        show-icon
        class="notice"
      />

      <el-card class="query-card" shadow="never">
        <el-form @submit.prevent>
          <el-form-item>
            <el-input
              v-model="keyword"
              placeholder="请输入卡号 / ICCID / 移动后6位 / 联通电信后2-7位"
              clearable
              @keyup.enter="handleQuery"
            >
              <template #append>
                <el-button type="primary" :loading="searching" @click="handleQuery">
                  查询
                </el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card v-if="candidates.length" class="panel" shadow="never">
        <template #header>请选择对应卡片</template>
        <div class="candidate-list">
          <button
            v-for="item in candidates"
            :key="item.id"
            class="candidate-item"
            @click="selectCandidate(item.id)"
          >
            <div class="candidate-title">{{ item.iccid_masked }}</div>
            <div class="candidate-meta">
              <span>{{ item.spec_name || '-' }}</span>
              <span>{{ item.status_name || '-' }}</span>
              <span>激活: {{ item.activated_at || '-' }}</span>
            </div>
          </button>
        </div>
      </el-card>

      <template v-if="detail">
        <el-card class="panel summary-panel" shadow="never">
          <template #header>核心信息</template>
          <div class="summary-grid">
            <div class="summary-item">
              <span>状态</span>
              <strong>{{ detail.card.status_name || detail.card.status || '-' }}</strong>
            </div>
            <div class="summary-item">
              <span>套餐</span>
              <strong>{{ detail.card.spec_name || '-' }}</strong>
            </div>
            <div class="summary-item">
              <span>使用率</span>
              <strong>{{ usagePercent.toFixed(2) }}%</strong>
            </div>
            <div class="summary-item">
              <span>剩余流量</span>
              <strong>{{ formatFlow(remainFlow) }}</strong>
            </div>
          </div>
        </el-card>

        <el-card class="panel" shadow="never">
          <template #header>卡片信息</template>
          <div class="info-grid">
            <div class="info-item"><span>ICCID</span><strong>{{ detail.card.iccid }}</strong></div>
            <div class="info-item"><span>卡号</span><strong>{{ detail.card.msisdn || '-' }}</strong></div>
            <div class="info-item"><span>套餐总量</span><strong>{{ formatFlow(detail.card.data_total) }}</strong></div>
            <div class="info-item"><span>本月已用</span><strong>{{ formatFlow(detail.card.data_used_month || 0) }}</strong></div>
            <div class="info-item"><span>累计已用</span><strong>{{ formatFlow(detail.card.data_used) }}</strong></div>
            <div class="info-item"><span>剩余流量</span><strong>{{ formatFlow(remainFlow) }}</strong></div>
            <div class="info-item"><span>激活时间</span><strong>{{ detail.card.activated_at || '-' }}</strong></div>
            <div class="info-item"><span>到期时间</span><strong>{{ detail.card.expired_at || '-' }}</strong></div>
            <div class="info-item"><span>最近同步</span><strong>{{ detail.card.data_sync_at || '-' }}</strong></div>
            <div class="info-item"><span>备注</span><strong>{{ detail.card.remark || '-' }}</strong></div>
          </div>
        </el-card>

        <el-card class="panel" shadow="never">
          <template #header>智能诊断</template>
          <el-empty v-if="!detail.diagnostics" description="暂无诊断数据" :image-size="64" />
          <div v-else class="diag-list">
            <div class="diag-item">
              <span>开机状态</span>
              <el-tag :type="detail.diagnostics.power_status_msg === '开机' ? 'success' : 'warning'">
                {{ detail.diagnostics.power_status_msg || '未知' }}
              </el-tag>
            </div>
            <div class="diag-item">
              <span>工作状态</span>
              <el-tag :type="detail.diagnostics.work_status_msg === '在线' ? 'success' : 'danger'">
                {{ detail.diagnostics.work_status_msg || '未知' }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <el-card class="panel" shadow="never">
          <template #header>操作</template>
          <div class="action-row">
            <el-button
              v-if="detail.actions.allow_suspend"
              type="warning"
              :loading="actionLoading === 'suspend'"
              @click="handleSuspend"
            >
              停机
            </el-button>
            <el-button
              v-if="detail.actions.allow_resume"
              type="success"
              :loading="actionLoading === 'resume'"
              @click="handleResume"
            >
              复机
            </el-button>
            <el-button
              v-if="detail.actions.allow_remark"
              type="primary"
              @click="remarkDialogVisible = true"
            >
              备注
            </el-button>
          </div>
        </el-card>
      </template>

      <el-card class="panel contact-panel" shadow="never">
        <template #header>客服信息</template>
        <div class="contact-item">电话：{{ config?.contact_phone || '-' }}</div>
        <div class="contact-item">微信：{{ config?.contact_wechat || '-' }}</div>
      </el-card>
    </div>

    <el-dialog v-model="remarkDialogVisible" title="修改备注" width="420px">
      <el-form @submit.prevent>
        <el-form-item label="备注">
          <el-input v-model="remarkForm.remark" type="textarea" :rows="4" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="remarkForm.operatorName" maxlength="50" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="remarkForm.operatorPhone" maxlength="20" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="remarkDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading === 'remark'" @click="handleRemarkSubmit">
          保存
        </el-button>
      </template>
    </el-dialog>

    <div
      v-if="detail && (detail.actions.allow_suspend || detail.actions.allow_resume || detail.actions.allow_remark)"
      class="mobile-action-bar"
    >
      <el-button
        v-if="detail.actions.allow_suspend"
        type="warning"
        :loading="actionLoading === 'suspend'"
        @click="handleSuspend"
      >
        停机
      </el-button>
      <el-button
        v-if="detail.actions.allow_resume"
        type="success"
        :loading="actionLoading === 'resume'"
        @click="handleResume"
      >
        复机
      </el-button>
      <el-button
        v-if="detail.actions.allow_remark"
        type="primary"
        @click="remarkDialogVisible = true"
      >
        备注
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { h5Api, type H5PortalConfig, type H5CardCandidate, type H5CardDetail } from '@/api/modules/h5'

const route = useRoute()
const slug = computed(() => String(route.params.slug || ''))

const config = ref<H5PortalConfig | null>(null)
const keyword = ref('')
const searching = ref(false)
const candidates = ref<H5CardCandidate[]>([])
const detail = ref<H5CardDetail | null>(null)
const actionLoading = ref<'suspend' | 'resume' | 'remark' | ''>('')
const remarkDialogVisible = ref(false)
const remarkForm = reactive({
  remark: '',
  operatorName: '',
  operatorPhone: ''
})

const heroStyle = computed(() => ({
  backgroundImage: config.value?.banner
    ? `linear-gradient(135deg, rgba(11, 61, 145, 0.78), rgba(16, 185, 129, 0.6)), url(${config.value.banner})`
    : 'linear-gradient(135deg, #0b3d91 0%, #0f766e 100%)'
}))
const remainFlow = computed(() => {
  if (!detail.value?.card) return 0
  return (detail.value.card.data_total || 0) - (detail.value.card.data_used || 0)
})
const usagePercent = computed(() => {
  if (!detail.value?.card?.data_total) return 0
  return ((detail.value.card.data_used || 0) / detail.value.card.data_total) * 100
})

const loadConfig = async () => {
  config.value = await h5Api.getConfig(slug.value)
}

const resetState = () => {
  candidates.value = []
  detail.value = null
}

const handleQuery = async () => {
  if (!keyword.value.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }

  searching.value = true
  resetState()
  try {
    const result = await h5Api.queryCard(slug.value, keyword.value.trim())
    if (result.match_type === 'none') {
      ElMessage.warning('未查询到对应卡片')
      return
    }

    if (result.match_type === 'fuzzy_multiple') {
      candidates.value = result.items as H5CardCandidate[]
      return
    }

    detail.value = (result.items[0] as H5CardDetail) || null
    if (detail.value) {
      remarkForm.remark = detail.value.card.remark || ''
    }
  } finally {
    searching.value = false
  }
}

const selectCandidate = async (cardId: number) => {
  detail.value = await h5Api.getCardDetail(slug.value, cardId)
  remarkForm.remark = detail.value.card.remark || ''
}

const refreshDetail = async () => {
  if (!detail.value?.card?.id) return
  detail.value = await h5Api.getCardDetail(slug.value, detail.value.card.id)
  remarkForm.remark = detail.value.card.remark || ''
}

const handleSuspend = async () => {
  if (!detail.value?.card?.id) return
  const promptResult: any = await ElMessageBox.prompt('可选填写停机原因', '停机确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPlaceholder: '请输入停机原因'
  }).catch(() => null)

  if (promptResult === null) return

  actionLoading.value = 'suspend'
  try {
    await h5Api.suspendCard(slug.value, detail.value.card.id, promptResult?.value || '')
    ElMessage.success('停机成功')
    await refreshDetail()
  } finally {
    actionLoading.value = ''
  }
}

const handleResume = async () => {
  if (!detail.value?.card?.id) return
  await ElMessageBox.confirm('确定要执行复机吗？', '复机确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })

  actionLoading.value = 'resume'
  try {
    await h5Api.resumeCard(slug.value, detail.value.card.id)
    ElMessage.success('复机成功')
    await refreshDetail()
  } finally {
    actionLoading.value = ''
  }
}

const handleRemarkSubmit = async () => {
  if (!detail.value?.card?.id) return
  actionLoading.value = 'remark'
  try {
    await h5Api.updateRemark(
      slug.value,
      detail.value.card.id,
      remarkForm.remark,
      remarkForm.operatorName,
      remarkForm.operatorPhone
    )
    ElMessage.success('备注已更新')
    remarkDialogVisible.value = false
    await refreshDetail()
  } finally {
    actionLoading.value = ''
  }
}

const formatFlow = (value: number) => {
  if (!value) return '0MB'
  if (value >= 1024) {
    const gb = value / 1024
    return Number.isInteger(gb) ? `${gb}GB` : `${gb.toFixed(2)}GB`
  }
  return `${value}MB`
}

onMounted(async () => {
  await loadConfig()
})
</script>

<style scoped lang="scss">
.h5-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top right, rgba(16, 185, 129, 0.12), transparent 28%),
    linear-gradient(180deg, #f4f8fb 0%, #edf3f7 100%);
  font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
}

.hero {
  position: relative;
  min-height: 198px;
  background-size: cover;
  background-position: center;
  color: #fff;
}

.hero__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(4, 18, 41, 0.18), rgba(4, 18, 41, 0.42));
}

.hero__content {
  position: relative;
  z-index: 1;
  max-width: 960px;
  margin: 0 auto;
  padding: 28px 18px 22px;
}

.hero__logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  object-fit: cover;
  margin-bottom: 14px;
  background: rgba(255, 255, 255, 0.92);
}

.hero__title {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
}

.hero__subtitle {
  margin-top: 8px;
  opacity: 0.92;
  font-size: 13px;
  line-height: 1.4;
}

.content {
  max-width: 960px;
  margin: -14px auto 0;
  padding: 0 14px 32px;
}

.notice,
.query-card,
.panel {
  margin-bottom: 12px;
  border-radius: 14px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.summary-item {
  padding: 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfeff 100%);
  border: 1px solid #d5eef8;
}

.summary-item span {
  display: block;
  margin-bottom: 6px;
  color: #4b5563;
  font-size: 12px;
}

.summary-item strong {
  color: #0f172a;
  font-size: 14px;
  word-break: break-all;
}

.candidate-list {
  display: grid;
  gap: 12px;
}

.candidate-item {
  width: 100%;
  padding: 14px;
  border: 1px solid #dbe5ee;
  border-radius: 14px;
  background: #fff;
  text-align: left;
  cursor: pointer;
}

.candidate-title {
  font-weight: 700;
  color: #10324a;
}

.candidate-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 8px;
  color: #5b7287;
  font-size: 13px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.info-item {
  padding: 12px;
  border-radius: 12px;
  background: #f7fafc;
}

.info-item span {
  display: block;
  margin-bottom: 6px;
  color: #6b7280;
  font-size: 13px;
}

.info-item strong {
  color: #0f172a;
  word-break: break-all;
}

.diag-list {
  display: grid;
  gap: 14px;
}

.diag-item,
.action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.action-row :deep(.el-button) {
  min-height: 40px;
  border-radius: 10px;
}

.mobile-action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: none;
  gap: 8px;
  padding: 10px 12px calc(10px + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.96);
  border-top: 1px solid #e5e7eb;
  box-shadow: 0 -10px 24px rgba(15, 23, 42, 0.09);
  z-index: 30;
}

.mobile-action-bar :deep(.el-button) {
  flex: 1;
  min-height: 42px;
  border-radius: 10px;
  font-weight: 600;
}

.contact-item + .contact-item {
  margin-top: 10px;
}

@media (max-width: 640px) {
  .hero {
    min-height: 178px;
  }

  .hero__title {
    font-size: 20px;
  }

  .hero__subtitle {
    font-size: 12px;
  }

  .content {
    padding: 0 10px 92px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .action-row {
    align-items: stretch;
    flex-direction: column;
  }

  .action-row :deep(.el-button) {
    width: 100%;
  }

  .mobile-action-bar {
    display: flex;
  }

  .panel :deep(.el-card__header) {
    padding: 12px 14px;
    font-size: 14px;
    font-weight: 600;
  }

  .panel :deep(.el-card__body) {
    padding: 12px 14px;
  }
}
</style>
