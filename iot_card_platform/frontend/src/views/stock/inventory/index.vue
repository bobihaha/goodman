<template>
  <div class="inventory-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">库存管理</span>
          <div>
            <el-button type="warning" @click="handleRecycle">
              <el-icon><RefreshLeft /></el-icon>
              卡片回收
            </el-button>
            <el-button type="primary" @click="handleStockOut">
              <el-icon><Sell /></el-icon>
              批量出库
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-label">库存总数</div>
              <div class="stat-value">{{ summary.stock_cards || 0 }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-label">已出库</div>
              <div class="stat-value">{{ summary.out_cards || 0 }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-label">中国移动</div>
              <div class="stat-value">{{ summary.by_carrier?.cmcc || 0 }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-label">中国联通</div>
              <div class="stat-value">{{ summary.by_carrier?.cucc || 0 }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="供应商">
          <el-select v-model="queryParams.supplier_id" placeholder="请选择供应商" clearable style="width: 200px">
            <el-option
              v-for="supplier in suppliers"
              :key="supplier.id"
              :label="supplier.name"
              :value="supplier.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="运营商">
          <el-select v-model="queryParams.carrier" placeholder="请选择运营商" clearable style="width: 150px">
            <el-option label="中国移动" value="cmcc" />
            <el-option label="中国联通" value="cucc" />
            <el-option label="中国电信" value="ctcc" />
          </el-select>
        </el-form-item>
        <el-form-item label="套餐">
          <el-select v-model="queryParams.package_id" placeholder="请选择套餐" clearable style="width: 200px">
            <el-option
              v-for="pkg in packages"
              :key="pkg.id"
              :label="pkg.name"
              :value="pkg.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-select v-model="queryParams.sort_by" placeholder="排序字段" clearable style="width: 150px">
            <el-option label="入库日期" value="stock_in_at" />
            <el-option label="测试期到期日" value="test_expire_date" />
            <el-option label="沉默期到期日" value="silent_expire_date" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序方式">
          <el-select v-model="queryParams.sort_order" placeholder="排序方式" style="width: 100px">
            <el-option label="升序" value="asc" />
            <el-option label="降序" value="desc" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 批量查询和导出 -->
      <div class="action-bar">
        <el-button type="primary" @click="showBatchQueryDialog = true">
          <el-icon><Search /></el-icon>
          批量查询
        </el-button>
        <el-button type="success" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出库存
        </el-button>
      </div>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="iccid" label="ICCID" width="200" fixed />
        <el-table-column prop="imsi" label="IMSI" width="150" />
        <el-table-column prop="msisdn" label="MSISDN" width="130" />
        <el-table-column prop="supplier_name" label="供应商" width="120" />
        <el-table-column label="规格" width="220">
          <template #default="{ row }">
            <el-tag>{{ row.carrier_name }}</el-tag>
            <el-tag type="success" style="margin-left: 5px">{{ formatFlow(row.flow_size) }}</el-tag>
            <el-tag type="info" style="margin-left: 5px">{{ row.period_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="生命周期" width="200">
          <template #default="{ row }">
            <div style="font-size: 12px; line-height: 1.6">
              <div v-if="row.test_expire_date">
                <el-tag size="small" type="warning">测试期</el-tag> {{ row.test_expire_date }}
              </div>
              <div>
                <el-tag size="small" type="info">沉默期</el-tag> {{ row.silent_expire_date }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="batch_no" label="批次号" width="150" />
        <el-table-column prop="stock_in_at" label="入库时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.stock_in_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status_name" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleViewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleQuery"
        @current-change="handleQuery"
        class="pagination"
      />
    </el-card>

    <!-- 批量查询对话框 -->
    <el-dialog
      v-model="showBatchQueryDialog"
      title="批量查询卡片"
      width="600px"
    >
      <el-alert
        title="批量查询说明"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <div>1. 每行输入一个ICCID，或使用逗号分隔</div>
        <div>2. 单次最多查询10000个卡号</div>
        <div>3. 查询结果将显示在下方表格中</div>
      </el-alert>

      <el-input
        v-model="batchQueryText"
        type="textarea"
        :rows="8"
        placeholder="请输入ICCID，每行一个或使用逗号分隔"
      />

      <div style="margin-top: 10px; color: #909399; font-size: 12px">
        已输入 {{ batchQueryCount }} 个卡号
      </div>

      <template #footer>
        <el-button @click="showBatchQueryDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBatchQuery" :loading="batchQuerying">
          查询
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量查询结果对话框 -->
    <el-dialog
      v-model="showBatchResultDialog"
      title="批量查询结果"
      width="900px"
    >
      <el-alert
        :title="`查询完成：找到 ${batchQueryResult.length} 张卡片，未找到 ${batchQueryNotFound.length} 个卡号`"
        :type="batchQueryNotFound.length > 0 ? 'warning' : 'success'"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <!-- 未找到的卡号 -->
      <div v-if="batchQueryNotFound.length > 0" style="margin-bottom: 20px">
        <div style="font-weight: 600; margin-bottom: 10px">未找到的卡号：</div>
        <el-tag v-for="iccid in batchQueryNotFound" :key="iccid" type="danger" style="margin: 5px">
          {{ iccid }}
        </el-tag>
      </div>

      <!-- 查询结果表格 -->
      <el-table :data="batchQueryResult" border stripe max-height="400">
        <el-table-column prop="iccid" label="ICCID" width="200" />
        <el-table-column prop="imsi" label="IMSI" width="150" />
        <el-table-column prop="msisdn" label="MSISDN" width="130" />
        <el-table-column prop="carrier_name" label="运营商" width="100" />
        <el-table-column prop="supplier_name" label="供应商" width="120" />
        <el-table-column prop="status_name" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status_name }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="showBatchResultDialog = false">关闭</el-button>
        <el-button type="success" @click="handleExportBatchResult">
          <el-icon><Download /></el-icon>
          导出结果
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Sell, Refresh, Search, Download, RefreshLeft } from '@element-plus/icons-vue'
import { stockApi } from '@/api/modules/stock'
import { supplierApi } from '@/api/modules/supplier'
import { packageApi } from '@/api/modules/package'
import { useRouter } from 'vue-router'
import * as XLSX from 'xlsx'

const router = useRouter()

// 查询参数
const queryParams = reactive({
  supplier_id: undefined,
  carrier: undefined,
  package_id: undefined,
  sort_by: 'stock_in_at',
  sort_order: 'desc',
  page: 1,
  page_size: 20
})

// 表格数据
const tableData = ref([])
const total = ref(0)
const loading = ref(false)

// 统计数据
const summary = ref<any>({})

// 供应商、套餐列表
const suppliers = ref([])
const packages = ref([])

// 批量查询
const showBatchQueryDialog = ref(false)
const showBatchResultDialog = ref(false)
const batchQueryText = ref('')
const batchQuerying = ref(false)
const batchQueryResult = ref<any[]>([])
const batchQueryNotFound = ref<string[]>([])

// 批量查询卡号数量
const batchQueryCount = computed(() => {
  if (!batchQueryText.value) return 0
  const iccids = batchQueryText.value
    .split(/[\n,，]/)
    .map(s => s.trim())
    .filter(s => s)
  return iccids.length
})

// 获取库存统计
const fetchSummary = async () => {
  try {
    const res = await stockApi.getSummary()
    summary.value = res
  } catch (error) {
    console.error('获取库存统计失败', error)
  }
}

// 获取库存列表
const fetchInventory = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory(queryParams)
    tableData.value = res.items || []  // 后端返回的是 items
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('获取库存列表失败')
  } finally {
    loading.value = false
  }
}

// 获取供应商列表
const fetchSuppliers = async () => {
  try {
    const res = await supplierApi.getList({ page: 1, page_size: 100 })
    suppliers.value = res.list || res.data?.items || res.data?.list || []
  } catch (error) {
    console.error('获取供应商列表失败', error)
  }
}

// 获取套餐列表
const fetchPackages = async () => {
  try {
    const res = await packageApi.getSalePackages({ page: 1, page_size: 100, status: 'enable' })
    packages.value = res.list || []  // 销售套餐API返回 list
  } catch (error) {
    console.error('获取套餐列表失败', error)
  }
}

// 查询
const handleQuery = () => {
  queryParams.page = 1
  fetchInventory()
}

// 重置
const handleReset = () => {
  queryParams.supplier_id = undefined
  queryParams.carrier = undefined
  queryParams.package_id = undefined
  queryParams.sort_by = 'stock_in_at'
  queryParams.sort_order = 'desc'
  queryParams.page = 1
  fetchInventory()
}

// 批量查询
const handleBatchQuery = async () => {
  if (!batchQueryText.value.trim()) {
    ElMessage.warning('请输入要查询的ICCID')
    return
  }

  // 解析ICCID列表
  const iccids = batchQueryText.value
    .split(/[\n,，]/)
    .map(s => s.trim())
    .filter(s => s)

  if (iccids.length === 0) {
    ElMessage.warning('请输入有效的ICCID')
    return
  }

  if (iccids.length > 10000) {
    ElMessage.warning('单次最多查询10000个卡号')
    return
  }

  batchQuerying.value = true
  try {
    const res = await stockApi.batchQuery({ iccids })
    batchQueryResult.value = res.found || []
    batchQueryNotFound.value = res.not_found || []
    
    showBatchQueryDialog.value = false
    showBatchResultDialog.value = true
    
    ElMessage.success(`查询完成：找到 ${batchQueryResult.value.length} 张卡片`)
  } catch (error: any) {
    ElMessage.error(error.message || '批量查询失败')
  } finally {
    batchQuerying.value = false
  }
}

// 导出库存
const handleExport = async () => {
  try {
    await ElMessageBox.confirm('确认导出当前筛选条件下的所有库存数据？', '导出确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    ElMessage.info('正在导出，请稍候...')
    
    const res = await stockApi.exportInventory(queryParams)
    
    // 创建工作簿并下载
    const ws = XLSX.utils.json_to_sheet(res)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '库存数据')
    XLSX.writeFile(wb, `库存数据_${new Date().getTime()}.xlsx`)
    
    ElMessage.success('导出成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '导出失败')
    }
  }
}

// 导出批量查询结果
const handleExportBatchResult = () => {
  if (batchQueryResult.value.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  const ws = XLSX.utils.json_to_sheet(batchQueryResult.value)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '查询结果')
  XLSX.writeFile(wb, `批量查询结果_${new Date().getTime()}.xlsx`)
  
  ElMessage.success('导出成功')
}

// 刷新
const handleRefresh = () => {
  fetchSummary()
  fetchInventory()
}

// 批量出库
const handleStockOut = () => {
  router.push('/stock/out')
}

// 卡片回收
const handleRecycle = () => {
  router.push('/stock/recycle')
}

// 查看详情
const handleViewDetail = (row: any) => {
  router.push(`/cards/detail/${row.id}`)
}

// 格式化流量
const formatFlow = (mb: number) => {
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(0)}GB`
  }
  return `${mb}MB`
}

// 格式化日期时间
const formatDateTime = (datetime: string) => {
  if (!datetime) return '-'
  return datetime.replace('T', ' ').substring(0, 16)
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
  fetchSummary()
  fetchInventory()
  fetchSuppliers()
  fetchPackages()
})
</script>

<style scoped lang="scss">
.inventory-container {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      font-size: 16px;
      font-weight: 600;
    }
  }

  .stats-row {
    margin-bottom: 20px;

    .stat-card {
      .stat-content {
        text-align: center;

        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-bottom: 10px;
        }

        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: #409eff;
        }
      }
    }
  }

  .search-form {
    margin-bottom: 20px;
  }

  .action-bar {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
  }

  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
}
</style>

