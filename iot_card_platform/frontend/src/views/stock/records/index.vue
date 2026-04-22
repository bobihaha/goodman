<template>
  <div class="records-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">出入库记录</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 入库记录 -->
        <el-tab-pane label="入库记录" name="in">
          <div class="records-section">
            <!-- 筛选 -->
            <el-form :inline="true" :model="inParams" class="search-form">
              <el-form-item label="供应商">
                <el-select v-model="inParams.supplier_id" placeholder="请选择" clearable style="width: 150px">
                  <el-option
                    v-for="supplier in suppliers"
                    :key="supplier.id"
                    :label="supplier.name"
                    :value="supplier.id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="入库时间">
                <el-date-picker
                  v-model="inDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 240px"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleQueryIn">查询</el-button>
                <el-button @click="handleResetIn">重置</el-button>
                <el-button type="success" @click="handleExportIn">
                  <el-icon><Download /></el-icon>
                  导出
                </el-button>
              </el-form-item>
            </el-form>

            <!-- 入库记录表格 -->
            <el-table :data="inRecords" v-loading="inLoading" border stripe>
              <el-table-column prop="id" label="记录ID" width="80" />
              <el-table-column prop="supplier_name" label="供应商" width="120" />
              <el-table-column prop="package_name" label="套餐" width="200" />
              <el-table-column prop="package_period" label="套餐周期" width="120">
                <template #default="{ row }">{{ row.package_period || '-' }}</template>
              </el-table-column>
              <el-table-column prop="card_count" label="入库数量" width="100">
                <template #default="{ row }">
                  <el-tag type="success">{{ row.card_count }} 张</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="test_expire_date" label="测试期截止" width="120" />
              <el-table-column prop="silent_expire_date" label="沉默期截止" width="120" />
              <el-table-column prop="operator_name" label="操作人" width="100" />
              <el-table-column prop="created_at" label="入库时间" width="160" />
              <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="handleViewInDetail(row)">
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <el-pagination
              v-model:current-page="inParams.page"
              v-model:page-size="inParams.page_size"
              :total="inTotal"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleQueryIn"
              @current-change="handleQueryIn"
              class="pagination"
            />
          </div>
        </el-tab-pane>

        <!-- 出库记录 -->
        <el-tab-pane label="出库记录" name="out">
          <div class="records-section">
            <!-- 筛选 -->
            <el-form :inline="true" :model="outParams" class="search-form">
              <el-form-item label="目标用户">
                <el-select v-model="outParams.user_id" placeholder="请选择" clearable style="width: 150px">
                  <el-option
                    v-for="user in users"
                    :key="user.id"
                    :label="user.name"
                    :value="user.id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="出库时间">
                <el-date-picker
                  v-model="outDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 240px"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleQueryOut">查询</el-button>
                <el-button @click="handleResetOut">重置</el-button>
                <el-button type="success" @click="handleExportOut">
                  <el-icon><Download /></el-icon>
                  导出
                </el-button>
              </el-form-item>
            </el-form>

            <!-- 出库记录表格 -->
            <el-table :data="outRecords" v-loading="outLoading" border stripe>
              <el-table-column prop="id" label="记录ID" width="80" />
              <el-table-column prop="record_no" label="出库单号" width="190" />
              <el-table-column prop="user_name" label="目标用户" width="120" />
              <el-table-column prop="sale_package_name" label="销售套餐" width="200" />
              <el-table-column prop="actual_period" label="开通周期" width="120">
                <template #default="{ row }">{{ row.actual_period || row.package_period || '-' }}</template>
              </el-table-column>
              <el-table-column prop="card_count" label="出库数量" width="100">
                <template #default="{ row }">
                  <el-tag type="warning">{{ row.card_count }} 张</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="total_amount" label="总金额" width="120">
                <template #default="{ row }">
                  <span style="color: #f56c6c; font-weight: 600">¥{{ row.total_amount }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="operator_name" label="操作人" width="100" />
              <el-table-column prop="created_at" label="出库时间" width="160" />
              <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="handleViewOutDetail(row)">
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <el-pagination
              v-model:current-page="outParams.page"
              v-model:page-size="outParams.page_size"
              :total="outTotal"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleQueryOut"
              @current-change="handleQueryOut"
              class="pagination"
            />
          </div>
        </el-tab-pane>

        <!-- 按卡号查询 -->
        <el-tab-pane label="按卡号查询" name="card">
          <div class="records-section">
            <el-form :inline="true" class="search-form">
              <el-form-item label="卡号">
                <el-input
                  v-model="cardIccid"
                  placeholder="输入ICCID查询"
                  clearable
                  style="width: 250px"
                  @keyup.enter="handleQueryCard"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleQueryCard">查询</el-button>
              </el-form-item>
            </el-form>

            <el-table :data="cardRecords" v-loading="cardLoading" border stripe>
              <el-table-column prop="record_type" label="类型" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.record_type === 'in' ? 'success' : 'warning'">
                    {{ row.record_type === 'in' ? '入库' : '出库' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="iccid" label="ICCID" width="180" />
              <el-table-column prop="supplier_name" label="供应商" width="120" />
              <el-table-column prop="base_package_name" label="底层套餐" width="150" />
              <el-table-column prop="sale_package_name" label="销售套餐" width="150" />
              <el-table-column prop="package_period" label="套餐周期" width="120">
                <template #default="{ row }">{{ row.package_period || '-' }}</template>
              </el-table-column>
              <el-table-column prop="target_user_name" label="目标用户" width="120" />
              <el-table-column prop="test_expire_date" label="测试期" width="110" />
              <el-table-column prop="silent_expire_date" label="沉默期" width="110" />
              <el-table-column prop="operator" label="操作人" width="100" />
              <el-table-column prop="created_at" label="操作时间" width="160" />
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 入库详情对话框 -->
    <el-dialog
      v-model="showInDetailDialog"
      title="入库记录详情"
      width="900px"
    >
      <el-descriptions :column="2" border v-if="currentInRecord">
        <el-descriptions-item label="记录ID">{{ currentInRecord.id }}</el-descriptions-item>
        <el-descriptions-item label="供应商">{{ currentInRecord.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="套餐">{{ currentInRecord.package_name }}</el-descriptions-item>
        <el-descriptions-item label="套餐周期">{{ currentInRecord.package_period || '-' }}</el-descriptions-item>
        <el-descriptions-item label="入库数量">
          <el-tag type="success">{{ currentInRecord.card_count }} 张</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="测试期截止">{{ currentInRecord.test_expire_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="沉默期截止">{{ currentInRecord.silent_expire_date }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ currentInRecord.operator_name }}</el-descriptions-item>
        <el-descriptions-item label="入库时间">{{ currentInRecord.created_at }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentInRecord.remark || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px">
        <div style="font-weight: 600; margin-bottom: 10px">入库卡片列表</div>
        <el-table :data="currentInRecord?.cards || []" border stripe max-height="300">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="iccid" label="ICCID" width="200" />
          <el-table-column prop="imsi" label="IMSI" width="150" />
          <el-table-column prop="msisdn" label="MSISDN" width="130" />
          <el-table-column prop="status_name" label="当前状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ row.status_name }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="showInDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 出库详情对话框 -->
    <el-dialog
      v-model="showOutDetailDialog"
      title="出库记录详情"
      width="900px"
    >
      <el-descriptions :column="2" border v-if="currentOutRecord">
        <el-descriptions-item label="记录ID">{{ currentOutRecord.id }}</el-descriptions-item>
        <el-descriptions-item label="出库单号">{{ currentOutRecord.record_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="目标用户">{{ currentOutRecord.user_name }}</el-descriptions-item>
        <el-descriptions-item label="销售套餐">{{ currentOutRecord.sale_package_name }}</el-descriptions-item>
        <el-descriptions-item label="开通周期">{{ currentOutRecord.actual_period || currentOutRecord.package_period || '-' }}</el-descriptions-item>
        <el-descriptions-item label="出库数量">
          <el-tag type="warning">{{ currentOutRecord.card_count }} 张</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="单价">¥{{ currentOutRecord.unit_price }}</el-descriptions-item>
        <el-descriptions-item label="总金额">
          <span style="color: #f56c6c; font-weight: 600">¥{{ currentOutRecord.total_amount }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="操作人">{{ currentOutRecord.operator_name }}</el-descriptions-item>
        <el-descriptions-item label="出库时间">{{ currentOutRecord.created_at }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentOutRecord.remark || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px">
        <div style="font-weight: 600; margin-bottom: 10px">出库卡片列表</div>
        <el-table :data="currentOutRecord?.cards || []" border stripe max-height="300">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="iccid" label="ICCID" width="200" />
          <el-table-column prop="imsi" label="IMSI" width="150" />
          <el-table-column prop="msisdn" label="MSISDN" width="130" />
          <el-table-column prop="status_name" label="当前状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ row.status_name }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="showOutDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { stockApi } from '@/api/modules/stock'
import { supplierApi } from '@/api/modules/supplier'
import { userApi } from '@/api/modules/user'
import * as XLSX from 'xlsx'

// 当前标签页
const activeTab = ref('in')

// 入库记录
const inParams = reactive({
  supplier_id: undefined,
  page: 1,
  page_size: 20
})
const inDateRange = ref<any[]>([])
const inRecords = ref<any[]>([])
const inTotal = ref(0)
const inLoading = ref(false)

// 出库记录
const outParams = reactive({
  user_id: undefined,
  page: 1,
  page_size: 20
})
const outDateRange = ref<any[]>([])
const outRecords = ref<any[]>([])
const outTotal = ref(0)
const outLoading = ref(false)

// 按卡号查询
const cardIccid = ref('')
const cardRecords = ref<any[]>([])
const cardLoading = ref(false)

// 供应商、用户列表
const suppliers = ref<any[]>([])
const users = ref<any[]>([])

// 详情对话框
const showInDetailDialog = ref(false)
const showOutDetailDialog = ref(false)
const currentInRecord = ref<any>(null)
const currentOutRecord = ref<any>(null)

// 获取供应商列表
const fetchSuppliers = async () => {
  try {
    const res = await supplierApi.getList({ page: 1, page_size: 100 })
    // 兼容不同的响应格式
    suppliers.value = res.list || []
  } catch (error) {
    console.error('获取供应商列表失败', error)
  }
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    const res = await userApi.getList({ page: 1, page_size: 100 })
    // 兼容不同的响应格式
    users.value = res.list || []
  } catch (error) {
    console.error('获取用户列表失败', error)
  }
}

// 查询入库记录
const handleQueryIn = async () => {
  inLoading.value = true
  try {
    const params: any = { ...inParams }
    if (inDateRange.value && inDateRange.value.length === 2) {
      params.start_date = inDateRange.value[0]
      params.end_date = inDateRange.value[1]
    }

    const res = await stockApi.getStockInRecords(params)
    // 响应拦截器已经返回了 data.data，所以直接访问 items
    inRecords.value = res.items || []
    inTotal.value = res.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    inLoading.value = false
  }
}

// 重置入库查询
const handleResetIn = () => {
  inParams.supplier_id = undefined
  inDateRange.value = []
  inParams.page = 1
  handleQueryIn()
}

// 导出入库记录
const handleExportIn = async () => {
  try {
    ElMessage.info('正在导出，请稍候...')
    
    const params: any = { ...inParams }
    if (inDateRange.value && inDateRange.value.length === 2) {
      params.start_date = inDateRange.value[0]
      params.end_date = inDateRange.value[1]
    }

    const res = await stockApi.exportStockInRecords(params)
    
    // 响应拦截器已经返回了 data.data
    const ws = XLSX.utils.json_to_sheet(res)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '入库记录')
    XLSX.writeFile(wb, `入库记录_${new Date().getTime()}.xlsx`)
    
    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  }
}

// 查询出库记录
const handleQueryOut = async () => {
  outLoading.value = true
  try {
    const params: any = { ...outParams }
    if (outDateRange.value && outDateRange.value.length === 2) {
      params.start_date = outDateRange.value[0]
      params.end_date = outDateRange.value[1]
    }

    const res = await stockApi.getStockOutRecords(params)
    // 响应拦截器已经返回了 data.data，所以直接访问 items
    outRecords.value = res.items || []
    outTotal.value = res.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    outLoading.value = false
  }
}

// 重置出库查询
const handleResetOut = () => {
  outParams.user_id = undefined
  outDateRange.value = []
  outParams.page = 1
  handleQueryOut()
}

// 按卡号查询
const handleQueryCard = async () => {
  if (!cardIccid.value.trim()) {
    ElMessage.warning('请输入ICCID')
    return
  }
  cardLoading.value = true
  try {
    const res = await stockApi.getCardStockRecords(cardIccid.value.trim())
    cardRecords.value = res.records || []
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    cardLoading.value = false
  }
}

// 导出出库记录
const handleExportOut = async () => {
  try {
    ElMessage.info('正在导出，请稍候...')
    
    const params: any = { ...outParams }
    if (outDateRange.value && outDateRange.value.length === 2) {
      params.start_date = outDateRange.value[0]
      params.end_date = outDateRange.value[1]
    }

    const res = await stockApi.exportStockOutRecords(params)
    
    // 响应拦截器已经返回了 data.data
    const ws = XLSX.utils.json_to_sheet(res)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '出库记录')
    XLSX.writeFile(wb, `出库记录_${new Date().getTime()}.xlsx`)
    
    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  }
}

// 查看入库详情
const handleViewInDetail = async (row: any) => {
  try {
    const res = await stockApi.getStockInDetail(row.id)
    // 响应拦截器已经返回了 data.data
    currentInRecord.value = res
    showInDetailDialog.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '获取详情失败')
  }
}

// 查看出库详情
const handleViewOutDetail = async (row: any) => {
  try {
    const res = await stockApi.getStockOutDetail(row.id)
    // 响应拦截器已经返回了 data.data
    currentOutRecord.value = res
    showOutDetailDialog.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '获取详情失败')
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    stock: 'info',
    testing: 'warning',
    silent: '',
    activated: 'success',
    expired: 'danger',
    suspended: 'danger'
  }
  return map[status] || 'info'
}

onMounted(() => {
  fetchSuppliers()
  fetchUsers()
  handleQueryIn()
  handleQueryOut()
})
</script>

<style scoped lang="scss">
.records-container {
  padding: 20px;

  .card-header {
    .title {
      font-size: 16px;
      font-weight: 600;
    }
  }

  .search-form {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
}
</style>
