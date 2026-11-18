<template>
  <el-card>
    <template #header><strong>订单记录</strong></template>
    <el-form inline @submit.prevent="search">
      <el-form-item label="订单日期">
        <el-date-picker v-model="dates" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" @change="search" />
      </el-form-item>
      <el-form-item><el-input v-model="number" placeholder="输入完整订单号" clearable @clear="search" /></el-form-item>
      <el-button native-type="submit" type="primary">查询</el-button>
    </el-form>
    <el-table :data="orders" empty-text="暂无订单记录">
      <el-table-column label="订单日期"><template #default="{ row }">{{ row.stock_out_date || '日期待核实' }}</template></el-table-column>
      <el-table-column prop="record_no" label="订单号" min-width="190" />
      <el-table-column prop="package_name" label="销售套餐" />
      <el-table-column prop="success_count" label="出库卡数" />
      <el-table-column prop="customer_remark" label="备注" min-width="180" show-overflow-tooltip />
      <el-table-column label="操作" width="220"><template #default="{ row }">
        <el-button link type="primary" @click="open(row)">查看卡片</el-button>
        <el-button link type="primary" @click="download(row)">下载卡号</el-button>
        <el-button link type="primary" @click="editRemark(row)">备注</el-button>
      </template></el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="total, prev, pager, next" @current-change="load" />

  </el-card>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { get, put } from '@/utils/request'
import { useAuthStore } from '@/stores/modules/auth'

interface Order { id: number; record_no: string; stock_out_date: string | null; package_name: string; success_count: number; customer_remark: string | null }
interface Page<T> { items: T[]; total: number }

const auth = useAuthStore()
const router = useRouter()
const orders = ref<Order[]>([])
const dates = ref<string[] | null>(null), number = ref('')
const page = ref(1), total = ref(0)
let orderRequest = 0

async function load() {
  const request = ++orderRequest
  const result = await get<Page<Order>>('/cards/orders', { params: {
    start: dates.value?.[0], end: dates.value?.[1], number: number.value, page: page.value
  } })
  if (request === orderRequest) { orders.value = result.items; total.value = result.total }
}
function search() { page.value = 1; load() }
function open(order: Order) {
  router.push({ path: '/cards/list', query: { batch_id: order.record_no } })
}
async function editRemark(order: Order) {
  const account = auth.userInfo?.id
  try {
    const resultBox = await ElMessageBox.prompt('最多 500 字，清空后保存可删除备注', '订单备注', {
      inputType: 'textarea', inputValue: order.customer_remark || '',
      inputValidator: value => (value || '').length <= 500 || '备注最多 500 字',
      confirmButtonText: '保存', cancelButtonText: '取消'
    })
    if (typeof resultBox === 'string' || auth.userInfo?.id !== account) return
    const value = resultBox.value
    const result = await put<{ customer_remark: string | null }>(
      '/cards/orders/' + order.id + '/remark', { remark: value || '' }
    )
    if (auth.userInfo?.id !== account) return
    order.customer_remark = result.customer_remark
    ElMessage.success('备注已保存')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') console.error('保存订单备注失败', error)
  }
}
async function download(order: Order) {
  const account = auth.userInfo?.id
  const numbers = await get<string[]>('/cards/orders/' + order.id + '/numbers')
  const XLSX = await import('xlsx')
  if (auth.userInfo?.id !== account) return
  const book = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(book, XLSX.utils.aoa_to_sheet([['ICCID'], ...numbers.map(n => [n])]), '卡号')
  XLSX.writeFile(book, (order.stock_out_date || '日期待核实') + '_' + order.record_no + '.xlsx')
}
watch(() => auth.userInfo?.id, id => {
  orderRequest++
  orders.value = []
  total.value = 0
  if (id) search()
}, { immediate: true })
</script>
