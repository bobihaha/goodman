<template>
  <div class="recycle-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">卡片回收</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 卡片回收 -->
        <el-tab-pane label="卡片回收" name="recycle">
          <div class="recycle-section">
            <el-alert
              title="回收说明"
              type="info"
              :closable="false"
              style="margin-bottom: 20px"
            >
              <div>1. 只有已出库的卡片才能回收</div>
              <div>2. 回收后卡片状态恢复为"库存"</div>
              <div>3. 回收操作需要填写回收原因</div>
              <div>4. 回收后的卡片可以重新出库</div>
            </el-alert>

            <!-- 搜索已出库卡片 -->
            <el-form :inline="true" :model="searchParams" class="search-form">
              <el-form-item label="ICCID">
                <el-input
                  v-model="searchParams.iccid"
                  placeholder="请输入ICCID"
                  clearable
                  style="width: 200px"
                  @keyup.enter="handleSearch"
                />
              </el-form-item>
              <el-form-item label="用户">
                <el-select v-model="searchParams.user_id" placeholder="请选择用户" clearable style="width: 200px">
                  <el-option
                    v-for="user in users"
                    :key="user.id"
                    :label="user.name"
                    :value="user.id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleSearch">查询</el-button>
                <el-button @click="handleResetSearch">重置</el-button>
              </el-form-item>
            </el-form>

            <!-- 已选卡片提示 -->
            <el-alert
              v-if="selectedCards.length > 0"
              :title="`已选择 ${selectedCards.length} 张卡片`"
              type="success"
              :closable="false"
              style="margin-bottom: 20px"
            />

            <!-- 已出库卡片列表 -->
            <el-table
              :data="outCards"
              v-loading="loading"
              border
              stripe
              @selection-change="handleSelectionChange"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="iccid" label="ICCID" width="200" />
              <el-table-column prop="imsi" label="IMSI" width="150" />
              <el-table-column prop="msisdn" label="MSISDN" width="130" />
              <el-table-column prop="user_name" label="所属用户" width="120" />
              <el-table-column prop="supplier_name" label="供应商" width="120" />
              <el-table-column label="规格" width="200">
                <template #default="{ row }">
                  {{ row.carrier_name }} / {{ formatFlow(row.flow_size) }} / {{ row.period_name }}
                </template>
              </el-table-column>
              <el-table-column prop="stock_out_at" label="出库时间" width="160" />
            </el-table>

            <!-- 分页 -->
            <el-pagination
              v-model:current-page="searchParams.page"
              v-model:page-size="searchParams.page_size"
              :total="total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSearch"
              @current-change="handleSearch"
              class="pagination"
            />

            <!-- 回收按钮 -->
            <div class="action-bar">
              <el-button
                type="danger"
                :disabled="selectedCards.length === 0"
                @click="showRecycleDialog = true"
              >
                回收选中卡片（{{ selectedCards.length }}）
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- 回收记录 -->
        <el-tab-pane label="回收记录" name="records">
          <div class="records-section">
            <!-- 筛选 -->
            <el-form :inline="true" :model="recordParams" class="search-form">
              <el-form-item label="回收时间">
                <el-date-picker
                  v-model="recordDateRange"
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
                <el-button type="primary" @click="handleQueryRecords">查询</el-button>
                <el-button @click="handleResetRecords">重置</el-button>
              </el-form-item>
            </el-form>

            <!-- 回收记录表格 -->
            <el-table :data="recycleRecords" v-loading="recordsLoading" border stripe>
              <el-table-column prop="id" label="记录ID" width="80" />
              <el-table-column prop="card_count" label="回收数量" width="100">
                <template #default="{ row }">
                  <el-tag type="success">{{ row.card_count }} 张</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="recycle_reason" label="回收原因" min-width="200" />
              <el-table-column prop="operator_name" label="操作人" width="120" />
              <el-table-column prop="created_at" label="回收时间" width="160" />
              <el-table-column prop="remark" label="备注" min-width="150" />
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="handleViewRecordDetail(row)">
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <el-pagination
              v-model:current-page="recordParams.page"
              v-model:page-size="recordParams.page_size"
              :total="recordTotal"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleQueryRecords"
              @current-change="handleQueryRecords"
              class="pagination"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 回收确认对话框 -->
    <el-dialog
      v-model="showRecycleDialog"
      title="确认回收"
      width="600px"
    >
      <el-alert
        :title="`即将回收 ${selectedCards.length} 张卡片，回收后卡片状态将恢复为"库存"`"
        type="warning"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <el-form :model="recycleForm" :rules="recycleRules" ref="recycleFormRef" label-width="100px">
        <el-form-item label="回收原因" prop="recycle_reason">
          <el-input
            v-model="recycleForm.recycle_reason"
            type="textarea"
            :rows="3"
            placeholder="请输入回收原因（必填）"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="recycleForm.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showRecycleDialog = false">取消</el-button>
        <el-button type="danger" @click="handleConfirmRecycle" :loading="recycling">
          确认回收
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { stockApi } from '@/api/modules/stock'
import { userApi } from '@/api/modules/user'

// 当前标签页
const activeTab = ref('recycle')

// 搜索参数
const searchParams = reactive({
  iccid: '',
  user_id: undefined,
  page: 1,
  page_size: 20
})

// 已出库卡片
const outCards = ref([])
const total = ref(0)
const loading = ref(false)

// 选中的卡片
const selectedCards = ref<any[]>([])

// 用户列表
const users = ref([])

// 回收对话框
const showRecycleDialog = ref(false)
const recycleForm = reactive({
  recycle_reason: '',
  remark: ''
})
const recycleRules = {
  recycle_reason: [{ required: true, message: '请输入回收原因', trigger: 'blur' }]
}
const recycleFormRef = ref()
const recycling = ref(false)

// 回收记录
const recordParams = reactive({
  page: 1,
  page_size: 20
})
const recordDateRange = ref([])
const recycleRecords = ref([])
const recordTotal = ref(0)
const recordsLoading = ref(false)

// 获取用户列表
const fetchUsers = async () => {
  try {
    const res = await userApi.getList({ page: 1, page_size: 100 })
    users.value = res.list || res.data?.items || res.data?.list || [] || []
  } catch (error) {
    console.error('获取用户列表失败', error)
  }
}

// 搜索已出库卡片
const handleSearch = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory({
      ...searchParams,
      status: 'out' // 只查询已出库的卡片
    })
    outCards.value = res.items || []  // 库存API返回 items
    total.value = res.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    loading.value = false
  }
}

// 重置搜索
const handleResetSearch = () => {
  searchParams.iccid = ''
  searchParams.user_id = undefined
  searchParams.page = 1
  handleSearch()
}

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedCards.value = selection
}

// 确认回收
const handleConfirmRecycle = async () => {
  if (!recycleFormRef.value) return
  
  const valid = await recycleFormRef.value.validate().catch(() => false)
  if (!valid) return

  try {
    await ElMessageBox.confirm(
      `确认回收 ${selectedCards.value.length} 张卡片？回收后卡片将恢复为库存状态。`,
      '二次确认',
      {
        confirmButtonText: '确定回收',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  recycling.value = true
  try {
    const card_ids = selectedCards.value.map(card => card.id)
    const res = await stockApi.recycleCards({
      card_ids,
      recycle_reason: recycleForm.recycle_reason,
      remark: recycleForm.remark
    })

    ElMessage.success(`回收成功！成功 ${res.success} 张，失败 ${res.failed} 张`)

    // 重置
    showRecycleDialog.value = false
    recycleForm.recycle_reason = ''
    recycleForm.remark = ''
    selectedCards.value = []

    // 刷新列表
    handleSearch()
    
    // 切换到回收记录标签页
    activeTab.value = 'records'
    handleQueryRecords()
  } catch (error: any) {
    ElMessage.error(error.message || '回收失败')
  } finally {
    recycling.value = false
  }
}

// 查询回收记录
const handleQueryRecords = async () => {
  recordsLoading.value = true
  try {
    const params: any = { ...recordParams }
    if (recordDateRange.value && recordDateRange.value.length === 2) {
      params.start_date = recordDateRange.value[0]
      params.end_date = recordDateRange.value[1]
    }

    const res = await stockApi.getRecycleRecords(params)
    recycleRecords.value = res.items || []  // 记录API返回 items
    recordTotal.value = res.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    recordsLoading.value = false
  }
}

// 重置回收记录查询
const handleResetRecords = () => {
  recordDateRange.value = []
  recordParams.page = 1
  handleQueryRecords()
}

// 查看回收记录详情
const handleViewRecordDetail = (row: any) => {
  ElMessageBox.alert(
    `<div>
      <p><strong>记录ID：</strong>${row.id}</p>
      <p><strong>回收数量：</strong>${row.card_count} 张</p>
      <p><strong>回收原因：</strong>${row.recycle_reason}</p>
      <p><strong>操作人：</strong>${row.operator_name}</p>
      <p><strong>回收时间：</strong>${row.created_at}</p>
      <p><strong>备注：</strong>${row.remark || '-'}</p>
    </div>`,
    '回收记录详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭'
    }
  )
}

// 格式化流量
const formatFlow = (mb: number) => {
  if (!mb) return '-'
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(0)}GB`
  }
  return `${mb}MB`
}

onMounted(() => {
  fetchUsers()
  handleSearch()
  handleQueryRecords()
})
</script>

<style scoped lang="scss">
.recycle-container {
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

  .action-bar {
    margin-top: 20px;
    text-align: center;
  }
}
</style>

