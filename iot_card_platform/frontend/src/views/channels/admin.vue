<template>
  <div class="channel-admin">
    <div class="page-header">
      <div>
        <h2>渠道积分管理</h2>
        <p>管理渠道报备、积分比例和逐笔订单积分。</p>
      </div>
      <el-button type="primary" @click="openCreate">新增渠道</el-button>
    </div>

    <el-card shadow="never" class="settings-card">
      <template #header><b>平台默认积分比例</b></template>
      <el-form inline :model="settings">
        <el-form-item label="出库比例">
          <el-input-number v-model="settings.default_stock_out_rate" :min="0" :max="100" :precision="4" />
          <span class="unit">%</span>
        </el-form-item>
        <el-form-item label="续费比例">
          <el-input-number v-model="settings.default_renewal_rate" :min="0" :max="100" :precision="4" />
          <span class="unit">%</span>
        </el-form-item>
        <el-form-item><el-button type="primary" :loading="savingSettings" @click="saveSettings">保存</el-button></el-form-item>
      </el-form>
      <div class="tip">比例修改只影响之后的新订单，历史积分保留原比例快照。</div>
    </el-card>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="渠道伙伴" name="partners">
        <el-card shadow="never">
          <div class="filters">
            <el-input v-model="partnerFilters.keyword" placeholder="渠道/联系人/手机号/账号" clearable style="width: 280px" @keyup.enter="loadPartners" />
            <el-select v-model="partnerFilters.status" placeholder="全部状态" clearable style="width: 130px">
              <el-option label="启用" value="enable" />
              <el-option label="停用" value="disable" />
            </el-select>
            <el-button type="primary" @click="loadPartners">查询</el-button>
          </div>
          <el-table v-loading="partnerLoading" :data="partners" border>
            <el-table-column prop="name" label="渠道" min-width="150" />
            <el-table-column label="联系人" min-width="160">
              <template #default="{ row }">{{ row.contact_name }} / {{ row.phone }}</template>
            </el-table-column>
            <el-table-column prop="account" label="登录账号" min-width="130" />
            <el-table-column prop="customer_count" label="客户数" width="90" align="center" />
            <el-table-column label="有效比例" min-width="170">
              <template #default="{ row }">出库 {{ formatRate(row.effective_stock_out_rate) }}% / 续费 {{ formatRate(row.effective_renewal_rate) }}%</template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }"><el-tag :type="row.status === 'enable' ? 'success' : 'info'">{{ row.status === 'enable' ? '启用' : '停用' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="300" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="copyH5(row)">复制H5</el-button>
                <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button link type="warning" @click="resetPassword(row)">重置密码</el-button>
                <el-button link :type="row.status === 'enable' ? 'danger' : 'success'" @click="toggleStatus(row)">{{ row.status === 'enable' ? '停用' : '启用' }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="积分明细" name="points">
        <el-card shadow="never">
          <div class="filters">
            <el-select v-model="pointFilters.channel_id" placeholder="全部渠道" clearable filterable style="width: 180px">
              <el-option v-for="item in partners" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
            <el-input v-model="pointFilters.keyword" placeholder="客户/手机号/订单号/ICCID" clearable style="width: 260px" />
            <el-select v-model="pointFilters.order_type" placeholder="全部订单" clearable style="width: 130px">
              <el-option label="出库" value="stock_out" /><el-option label="续费" value="renewal" />
            </el-select>
            <el-select v-model="pointFilters.status" placeholder="全部状态" clearable style="width: 130px">
              <el-option label="待结算" value="pending" /><el-option label="已结算" value="settled" />
            </el-select>
            <el-date-picker v-model="pointFilters.date_range" type="daterange" value-format="YYYY-MM-DD" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" style="width: 250px" />
            <el-button type="primary" @click="searchPoints">查询</el-button>
            <el-button type="success" :disabled="selectedPendingIds.length === 0" @click="settleSelected">确认结算（{{ selectedPendingIds.length }}）</el-button>
          </div>
          <el-table v-loading="pointLoading" :data="points" border @selection-change="selectedPoints = $event">
            <el-table-column type="selection" width="45" :selectable="canSelectPoint" />
            <el-table-column prop="channel_name" label="渠道" min-width="120" />
            <el-table-column label="客户" min-width="160"><template #default="{ row }">{{ row.customer_name }}<br><span class="muted">{{ row.customer_phone }}</span></template></el-table-column>
            <el-table-column label="订单" min-width="185"><template #default="{ row }"><el-tag size="small" :type="row.order_type === 'renewal' ? 'success' : ''">{{ orderLabel(row.order_type) }}</el-tag> {{ row.source_order_no }}</template></el-table-column>
            <el-table-column prop="iccid" label="ICCID" min-width="190" />
            <el-table-column label="计佣基数" width="110" align="right"><template #default="{ row }">{{ formatNumber(row.base_amount) }}</template></el-table-column>
            <el-table-column label="比例" width="90" align="right"><template #default="{ row }">{{ formatRate(row.rate_percent) }}%</template></el-table-column>
            <el-table-column label="积分" width="110" align="right"><template #default="{ row }"><span :class="{ negative: row.points < 0 }">{{ formatNumber(row.points) }}</span></template></el-table-column>
            <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.status === 'settled' ? 'success' : 'warning'">{{ row.status === 'settled' ? '已结算' : '待结算' }}</el-tag></template></el-table-column>
            <el-table-column prop="created_at" label="产生时间" width="170" />
          </el-table>
          <div class="pagination"><el-pagination v-model:current-page="pointPage.page" v-model:page-size="pointPage.page_size" :total="pointPage.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next" @change="loadPoints" /></div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="partnerDialog" :title="editingPartner ? '编辑渠道' : '新增渠道'" width="620px" destroy-on-close>
      <el-form ref="partnerFormRef" :model="partnerForm" :rules="partnerRules" label-width="120px">
        <el-form-item label="渠道名称" prop="name"><el-input v-model="partnerForm.name" /></el-form-item>
        <el-form-item label="联系人" prop="contact_name"><el-input v-model="partnerForm.contact_name" /></el-form-item>
        <el-form-item label="手机号" prop="phone"><el-input v-model="partnerForm.phone" maxlength="11" /></el-form-item>
        <el-form-item v-if="!editingPartner" label="登录账号" prop="account"><el-input v-model="partnerForm.account" /></el-form-item>
        <el-form-item v-if="!editingPartner" label="初始密码" prop="password"><el-input v-model="partnerForm.password" type="password" show-password /></el-form-item>
        <el-form-item label="出库比例覆盖"><el-input-number v-model="partnerForm.stock_out_rate_override" :min="0" :max="100" :precision="4" clearable /><span class="unit">%</span><span class="form-tip">留空使用平台默认</span></el-form-item>
        <el-form-item label="续费比例覆盖"><el-input-number v-model="partnerForm.renewal_rate_override" :min="0" :max="100" :precision="4" clearable /><span class="unit">%</span><span class="form-tip">留空使用平台默认</span></el-form-item>
        <el-form-item label="允许客户报备"><el-switch v-model="partnerForm.registration_enabled" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="partnerForm.remark" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="partnerDialog = false">取消</el-button><el-button type="primary" :loading="partnerSaving" @click="savePartner">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { channelAdminApi } from '@/api/modules/channel'
import type { ChannelPartner, ChannelPointItem } from '@/types/channel'

const activeTab = ref('partners')
const settings = reactive({ default_stock_out_rate: 0, default_renewal_rate: 0 })
const savingSettings = ref(false)
const partners = ref<ChannelPartner[]>([])
const partnerLoading = ref(false)
const partnerFilters = reactive({ keyword: '', status: '' })
const partnerDialog = ref(false)
const partnerSaving = ref(false)
const editingPartner = ref<ChannelPartner | null>(null)
const partnerFormRef = ref<FormInstance>()
const emptyPartner = () => ({ name: '', contact_name: '', phone: '', account: '', password: '', stock_out_rate_override: null as number | null, renewal_rate_override: null as number | null, registration_enabled: true, remark: '' })
const partnerForm = reactive(emptyPartner())
const partnerRules: FormRules = {
  name: [{ required: true, message: '请输入渠道名称' }], contact_name: [{ required: true, message: '请输入联系人' }],
  phone: [{ required: true, pattern: /^1[3-9]\d{9}$/, message: '请输入正确手机号' }],
  account: [{ required: true, pattern: /^[A-Za-z0-9_]{4,50}$/, message: '4-50位字母数字下划线' }],
  password: [{ required: true, min: 8, message: '至少8位且需包含大小写字母和数字' }]
}
const points = ref<ChannelPointItem[]>([])
const pointLoading = ref(false)
const pointFilters = reactive({ channel_id: undefined as number | undefined, keyword: '', order_type: '', status: '', date_range: [] as string[] })
const pointPage = reactive({ page: 1, page_size: 20, total: 0 })
const selectedPoints = ref<ChannelPointItem[]>([])
const selectedPendingIds = computed(() => selectedPoints.value.filter(item => item.status === 'pending').map(item => item.id))
const canSelectPoint = (row: ChannelPointItem) => row.status === 'pending'
const formatNumber = (value: number) => Number(value || 0).toFixed(2)
const formatRate = (value: number) => Number(value || 0).toFixed(2).replace(/\.00$/, '')
const orderLabel = (type: string) => type === 'renewal' ? '续费' : '出库'

const loadSettings = async () => Object.assign(settings, await channelAdminApi.getSettings())
const saveSettings = async () => { savingSettings.value = true; try { await channelAdminApi.updateSettings(settings); ElMessage.success('默认比例已保存'); await loadPartners() } finally { savingSettings.value = false } }
const loadPartners = async () => { partnerLoading.value = true; try { partners.value = (await channelAdminApi.getPartners(partnerFilters)).items } finally { partnerLoading.value = false } }
const openCreate = () => { editingPartner.value = null; Object.assign(partnerForm, emptyPartner()); partnerDialog.value = true }
const openEdit = (row: ChannelPartner) => { editingPartner.value = row; Object.assign(partnerForm, { name: row.name, contact_name: row.contact_name, phone: row.phone, account: row.account, password: '', stock_out_rate_override: row.stock_out_rate_override, renewal_rate_override: row.renewal_rate_override, registration_enabled: row.registration_enabled, remark: row.remark || '' }); partnerDialog.value = true }
const savePartner = async () => { await partnerFormRef.value?.validate(); partnerSaving.value = true; try { const data = { ...partnerForm }; if (editingPartner.value) { delete (data as any).account; delete (data as any).password; await channelAdminApi.updatePartner(editingPartner.value.id, data) } else await channelAdminApi.createPartner(data); ElMessage.success('渠道已保存'); partnerDialog.value = false; await loadPartners() } finally { partnerSaving.value = false } }
const copyH5 = async (row: ChannelPartner) => { await navigator.clipboard.writeText(`${window.location.origin}${row.h5_path}`); ElMessage.success('H5地址已复制') }
const resetPassword = async (row: ChannelPartner) => { const result = await ElMessageBox.prompt('请输入新密码（包含大小写字母和数字）', `重置 ${row.name} 密码`, { inputType: 'password', inputPattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,20}$/, inputErrorMessage: '需为8-20位且包含大小写字母和数字' }); await channelAdminApi.resetPassword(row.id, (result as any).value); ElMessage.success('密码已重置') }
const toggleStatus = async (row: ChannelPartner) => { const status = row.status === 'enable' ? 'disable' : 'enable'; await ElMessageBox.confirm(`${status === 'disable' ? '停用后将停止登录、报备和新增积分' : '确认重新启用'}？`, '确认操作'); await channelAdminApi.updatePartner(row.id, { status }); await loadPartners() }
const loadPoints = async () => { pointLoading.value = true; try { const { date_range, ...filters } = pointFilters; const res = await channelAdminApi.getPoints({ ...filters, start_time: date_range?.[0] ? `${date_range[0]}T00:00:00` : undefined, end_time: date_range?.[1] ? `${date_range[1]}T23:59:59` : undefined, page: pointPage.page, page_size: pointPage.page_size }); points.value = res.items; pointPage.total = res.total } finally { pointLoading.value = false } }
const searchPoints = () => { pointPage.page = 1; loadPoints() }
const settleSelected = async () => { await ElMessageBox.confirm(`确认结算选中的 ${selectedPendingIds.value.length} 条积分？`, '确认结算'); await channelAdminApi.settlePoints(selectedPendingIds.value); ElMessage.success('结算状态已更新'); await loadPoints() }

watch(activeTab, tab => { if (tab === 'points') loadPoints() })
onMounted(async () => { await Promise.all([loadSettings(), loadPartners()]) })
</script>

<style scoped>
.channel-admin{padding:20px}.page-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px}.page-header h2{margin:0 0 8px}.page-header p,.tip,.muted,.form-tip{color:#909399}.settings-card{margin-bottom:16px}.filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}.unit{margin-left:6px}.form-tip{margin-left:10px;font-size:12px}.negative{color:#f56c6c}.pagination{display:flex;justify-content:flex-end;margin-top:16px}
</style>
