<template>
  <div class="points-page">
    <header>
      <div>
        <h1>{{ partner?.name || '渠道积分中心' }}</h1>
        <p>查看已推荐客户、用户情况和订单积分</p>
      </div>
      <div class="header-actions">
        <el-button v-if="partner?.h5_path" type="primary" plain @click="openRegister">客户登记页</el-button>
        <el-button @click="logout">退出登录</el-button>
      </div>
    </header>

    <div class="summary-grid">
      <el-card v-for="item in summaryCards" :key="item.label" shadow="never">
        <div class="summary-label">{{ item.label }}</div>
        <div class="summary-value">{{ item.value }}</div>
      </el-card>
    </div>
    <p class="summary-tip">已消耗积分为平台已确认结算积分，剩余积分为当前待结算积分。</p>

    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="推荐客户" name="customers">
          <div class="filters">
            <el-input
              v-model="customerFilters.keyword"
              placeholder="客户、手机号、设备或场景"
              clearable
              class="keyword-input"
              @keyup.enter="searchCustomers"
            />
            <el-button type="primary" @click="searchCustomers">查询</el-button>
          </div>
          <el-table v-loading="customerLoading" :data="customers" border>
            <el-table-column label="客户" min-width="150">
              <template #default="{ row }">
                {{ row.customer_name }}<br><span class="muted">{{ row.customer_phone }}</span>
              </template>
            </el-table-column>
            <el-table-column label="用户情况" min-width="260">
              <template #default="{ row }"><span class="profile">{{ row.customer_profile || '—' }}</span></template>
            </el-table-column>
            <el-table-column prop="registered_at" label="推荐时间" width="170" />
            <el-table-column prop="point_count" label="积分笔数" width="90" align="right" />
            <el-table-column label="累计积分" width="110" align="right">
              <template #default="{ row }">{{ num(row.total_points) }}</template>
            </el-table-column>
            <el-table-column label="已消耗" width="110" align="right">
              <template #default="{ row }">{{ num(row.consumed_points) }}</template>
            </el-table-column>
            <el-table-column label="剩余积分" width="110" align="right">
              <template #default="{ row }"><b>{{ num(row.remaining_points) }}</b></template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              v-model:current-page="customerPage.page"
              v-model:page-size="customerPage.page_size"
              :total="customerPage.total"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              @current-change="loadCustomers"
              @size-change="searchCustomers"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="订单积分明细" name="points">
          <div class="filters">
            <el-input v-model="pointFilters.keyword" placeholder="客户/手机号/订单号/ICCID" clearable class="keyword-input" @keyup.enter="searchPoints" />
            <el-select v-model="pointFilters.order_type" placeholder="全部订单" clearable style="width:130px">
              <el-option label="出库" value="stock_out" />
              <el-option label="续费" value="renewal" />
            </el-select>
            <el-select v-model="pointFilters.status" placeholder="全部状态" clearable style="width:130px">
              <el-option label="剩余/待结算" value="pending" />
              <el-option label="已消耗/已结算" value="settled" />
            </el-select>
            <el-date-picker v-model="pointFilters.date_range" type="daterange" value-format="YYYY-MM-DD" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" style="width:250px" />
            <el-button type="primary" @click="searchPoints">查询</el-button>
          </div>
          <el-table v-loading="pointLoading" :data="points" border>
            <el-table-column label="客户" min-width="160">
              <template #default="{ row }">{{ row.customer_name }}<br><span class="muted">{{ row.customer_phone }}</span></template>
            </el-table-column>
            <el-table-column label="订单" min-width="190">
              <template #default="{ row }">
                <el-tag size="small" :type="row.order_type === 'renewal' ? 'success' : 'primary'">{{ row.order_type === 'renewal' ? '续费' : '出库' }}</el-tag>
                {{ row.source_order_no }}
              </template>
            </el-table-column>
            <el-table-column prop="iccid" label="ICCID" min-width="190" />
            <el-table-column label="计佣基数" width="110" align="right"><template #default="{ row }">{{ num(row.base_amount) }}</template></el-table-column>
            <el-table-column label="比例" width="90" align="right"><template #default="{ row }">{{ num(row.rate_percent) }}%</template></el-table-column>
            <el-table-column label="积分" width="110" align="right"><template #default="{ row }"><b :class="{ negative: row.points < 0 }">{{ num(row.points) }}</b></template></el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }"><el-tag :type="row.status === 'settled' ? 'success' : 'warning'">{{ row.status === 'settled' ? '已消耗' : '剩余' }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="created_at" label="产生时间" width="170" />
          </el-table>
          <div class="pagination">
            <el-pagination
              v-model:current-page="pointPage.page"
              v-model:page-size="pointPage.page_size"
              :total="pointPage.total"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              @current-change="loadPoints"
              @size-change="searchPoints"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { channelPortalApi } from '@/api/modules/channel'
import type { ChannelCustomerItem, ChannelPointItem, ChannelPointSummary } from '@/types/channel'

const router = useRouter()
const partner = ref<{ id: number; name: string; h5_path: string } | null>(null)
const activeTab = ref('customers')
const summary = ref<ChannelPointSummary>({
  customer_count: 0,
  total_points: 0,
  pending_points: 0,
  settled_points: 0,
  consumed_points: 0,
  remaining_points: 0,
  month_points: 0
})
const customers = ref<ChannelCustomerItem[]>([])
const points = ref<ChannelPointItem[]>([])
const customerLoading = ref(false)
const pointLoading = ref(false)
const customerFilters = reactive({ keyword: '' })
const pointFilters = reactive({ keyword: '', order_type: '', status: '', date_range: [] as string[] })
const customerPage = reactive({ page: 1, page_size: 20, total: 0 })
const pointPage = reactive({ page: 1, page_size: 20, total: 0 })
const num = (value: number) => Number(value || 0).toFixed(2)

const summaryCards = computed(() => [
  { label: '已推荐客户', value: `${summary.value.customer_count} 位` },
  { label: '累计积分', value: num(summary.value.total_points) },
  { label: '已消耗积分', value: num(summary.value.consumed_points) },
  { label: '剩余积分', value: num(summary.value.remaining_points) },
  { label: '本月新增', value: num(summary.value.month_points) }
])

const logout = () => {
  localStorage.removeItem('channel_access_token')
  localStorage.removeItem('channel_partner')
  router.replace('/channel/login')
}
const openRegister = () => window.open(partner.value?.h5_path, '_blank', 'noopener')
const handleLoadError = (error: any) => {
  ElMessage.error(error.message || '加载失败')
  if (/登录|认证|401/.test(error.message || '')) logout()
}
const loadCustomers = async () => {
  customerLoading.value = true
  try {
    const result = await channelPortalApi.customers({
      keyword: customerFilters.keyword,
      page: customerPage.page,
      page_size: customerPage.page_size
    })
    customers.value = result.items
    customerPage.total = result.total
  } catch (error: any) {
    handleLoadError(error)
  } finally {
    customerLoading.value = false
  }
}
const searchCustomers = () => {
  customerPage.page = 1
  loadCustomers()
}
const loadPoints = async () => {
  pointLoading.value = true
  try {
    const { date_range, ...query } = pointFilters
    const result = await channelPortalApi.points({
      ...query,
      start_time: date_range?.[0] ? `${date_range[0]}T00:00:00` : undefined,
      end_time: date_range?.[1] ? `${date_range[1]}T23:59:59` : undefined,
      page: pointPage.page,
      page_size: pointPage.page_size
    })
    points.value = result.items
    pointPage.total = result.total
  } catch (error: any) {
    handleLoadError(error)
  } finally {
    pointLoading.value = false
  }
}
const searchPoints = () => {
  pointPage.page = 1
  loadPoints()
}

onMounted(async () => {
  if (!localStorage.getItem('channel_access_token')) return logout()
  try {
    partner.value = await channelPortalApi.me()
    summary.value = await channelPortalApi.summary()
    await Promise.all([loadCustomers(), loadPoints()])
  } catch (error: any) {
    ElMessage.error(error.message || '登录已失效')
    logout()
  }
})
</script>

<style scoped>
.points-page{min-height:100vh;padding:28px;background:#f5f7fa}header{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:20px}h1{margin:0 0 6px}header p,.muted,.summary-tip{color:#909399}.header-actions{display:flex;gap:10px}.summary-grid{display:grid;grid-template-columns:repeat(5,minmax(150px,1fr));gap:14px}.summary-label{color:#909399}.summary-value{font-size:26px;font-weight:700;margin-top:10px}.summary-tip{margin:10px 0 18px;font-size:13px}.filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}.keyword-input{width:280px}.profile{white-space:pre-wrap;line-height:1.6}.negative{color:#f56c6c}.pagination{display:flex;justify-content:flex-end;margin-top:16px}
@media(max-width:900px){.points-page{padding:16px}header{align-items:stretch;flex-direction:column}.header-actions{justify-content:flex-end}.summary-grid{grid-template-columns:repeat(2,1fr)}.keyword-input{width:100%}.pagination{overflow-x:auto;justify-content:flex-start}}
</style>
