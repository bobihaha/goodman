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
              title="回收说明：只有已分配用户的卡片才能回收，回收后卡片状态恢复为库存，可重新出库。"
              type="info"
              :closable="false"
              style="margin-bottom: 16px"
            />

            <!-- 搜索 -->
            <el-form :inline="true" class="search-form">
              <el-form-item label="ICCID/号码">
                <el-input
                  v-model="searchParams.keyword"
                  placeholder="输入ICCID或号码"
                  clearable
                  style="width: 220px"
                  @keyup.enter="handleSearch"
                />
              </el-form-item>
              <el-form-item label="状态">
                <el-select v-model="searchParams.status" placeholder="全部状态" clearable style="width: 140px">
                  <el-option label="已激活" value="activated" />
                  <el-option label="测试期" value="testing" />
                  <el-option label="沉默期" value="silent" />
                  <el-option label="已停机" value="suspended" />
                  <el-option label="已过期" value="expired" />
                </el-select>
              </el-form-item>
              <el-form-item label="运营商">
                <el-select v-model="searchParams.carrier" placeholder="全部" clearable style="width: 120px">
                  <el-option label="中国移动" value="cmcc" />
                  <el-option label="中国联通" value="cucc" />
                  <el-option label="中国电信" value="ctcc" />
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
              :title="'已选择 ' + selectedCards.length + ' 张卡片'"
              type="success"
              :closable="false"
              style="margin-bottom: 12px"
            />

            <!-- 卡片列表 -->
            <el-table
              :data="outCards"
              v-loading="loading"
              border
              stripe
              @selection-change="handleSelectionChange"
            >
              <el-table-column type="selection" width="50" />
              <el-table-column prop="iccid" label="ICCID" min-width="180" show-overflow-tooltip />
              <el-table-column prop="msisdn" label="号码" width="130" />
              <el-table-column prop="carrier" label="运营商" width="90">
                <template #default="{ row }">
                  {{ formatCarrier(row.carrier) }}
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusName(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="流量" width="100">
                <template #default="{ row }">
                  {{ formatFlow(row.flow_size) }}
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

        <!-- 批量粘贴回收 -->
        <el-tab-pane label="批量粘贴回收" name="paste">
          <div class="paste-section">
            <el-alert
              title="支持批量粘贴 ICCID，每行一个，也可使用空格或中英文逗号分隔。系统会自动去重。"
              type="info"
              :closable="false"
              style="margin-bottom: 16px"
            />

            <el-input
              v-model="pasteIccidText"
              type="textarea"
              :rows="12"
              placeholder="请输入 ICCID，每行一个&#10;例如：&#10;89860123456789012345&#10;89860123456789012346"
            />

            <div class="batch-input-info">
              <span>有效 ICCID：<strong>{{ pasteIccids.length }}</strong> 条</span>
              <span v-if="invalidPasteIccids.length" class="error-text">
                无效内容 {{ invalidPasteIccids.length }} 条，请检查纯数字且不少于 10 位
              </span>
              <span v-else-if="pasteEntries.length > BATCH_RECYCLE_MAX_COUNT" class="error-text">
                超出限制，单次最多 {{ BATCH_RECYCLE_MAX_COUNT }} 条
              </span>
            </div>

            <div class="action-bar">
              <el-button
                type="danger"
                :disabled="pasteIccids.length === 0 || invalidPasteIccids.length > 0 || pasteEntries.length > BATCH_RECYCLE_MAX_COUNT"
                @click="openPasteRecycleDialog"
              >
                批量回收（{{ pasteIccids.length }}）
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- Excel批量回收 -->
        <el-tab-pane label="Excel批量回收" name="excel">
          <div class="excel-section">
            <el-alert
              title="上传包含ICCID的Excel文件，系统将自动识别并批量回收。Excel第一列应为ICCID。"
              type="info"
              :closable="false"
              style="margin-bottom: 16px"
            />

            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              drag
            >
              <el-icon :size="40" style="color: #8c8c8c"><UploadFilled /></el-icon>
              <div style="margin-top: 8px">将Excel文件拖到此处，或<em>点击上传</em></div>
              <template #tip>
                <div style="color: #8c8c8c; font-size: 12px">仅支持 .xlsx / .xls 格式</div>
              </template>
            </el-upload>

            <!-- 解析结果预览 -->
            <div v-if="excelIccids.length > 0" style="margin-top: 16px">
              <el-alert
                :title="'已解析 ' + excelIccids.length + ' 个ICCID'"
                type="success"
                :closable="false"
                style="margin-bottom: 12px"
              />
              <el-table :data="excelIccids.slice(0, 20)" border stripe max-height="300">
                <el-table-column type="index" label="#" width="60" />
                <el-table-column prop="iccid" label="ICCID" />
              </el-table>
              <p v-if="excelIccids.length > 20" style="color: #8c8c8c; font-size: 12px; margin-top: 8px">
                仅显示前20条，共 {{ excelIccids.length }} 条
              </p>

              <div class="action-bar">
                <el-button type="danger" @click="showExcelRecycleDialog = true">
                  批量回收（{{ excelIccids.length }}）
                </el-button>
              </div>
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
        :title="'即将回收 ' + selectedCards.length + ' 张卡片，回收后卡片状态将恢复为【库存】'"
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

    <!-- 批量粘贴回收确认对话框 -->
    <el-dialog
      v-model="showPasteRecycleDialog"
      title="批量粘贴回收确认"
      width="600px"
    >
      <el-alert
        :title="'即将通过 ICCID 批量回收 ' + pasteIccids.length + ' 张卡片，回收后卡片状态将恢复为【库存】'"
        type="warning"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <el-form :model="pasteRecycleForm" :rules="recycleRules" ref="pasteRecycleFormRef" label-width="100px">
        <el-form-item label="回收原因" prop="recycle_reason">
          <el-input
            v-model="pasteRecycleForm.recycle_reason"
            type="textarea"
            :rows="3"
            placeholder="请输入回收原因（必填）"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="pasteRecycleForm.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showPasteRecycleDialog = false">取消</el-button>
        <el-button type="danger" @click="handlePasteRecycle" :loading="recycling">
          确认回收
        </el-button>
      </template>
    </el-dialog>

    <!-- Excel批量回收确认对话框 -->
    <el-dialog
      v-model="showExcelRecycleDialog"
      title="Excel批量回收确认"
      width="600px"
    >
      <el-alert
        :title="'即将通过ICCID批量回收 ' + excelIccids.length + ' 张卡片'"
        type="warning"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <el-form :model="excelRecycleForm" :rules="recycleRules" ref="excelRecycleFormRef" label-width="100px">
        <el-form-item label="回收原因" prop="recycle_reason">
          <el-input
            v-model="excelRecycleForm.recycle_reason"
            type="textarea"
            :rows="3"
            placeholder="请输入回收原因（必填）"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="excelRecycleForm.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showExcelRecycleDialog = false">取消</el-button>
        <el-button type="danger" @click="handleExcelRecycle" :loading="recycling">
          确认回收
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { stockApi } from '@/api/modules/stock'
import { cardApi } from '@/api/modules/card'

// 当前标签页
const activeTab = ref('recycle')

// 搜索参数 - 使用 /cards API 的参数格式
const searchParams = reactive({
  keyword: '',
  status: '',
  carrier: '',
  page: 1,
  page_size: 20
})

// 已出库卡片
const outCards = ref<any[]>([])
const total = ref(0)
const loading = ref(false)

// 选中的卡片
const selectedCards = ref<any[]>([])

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

// 批量粘贴回收
const BATCH_RECYCLE_MAX_COUNT = 10000
const pasteIccidText = ref('')
const showPasteRecycleDialog = ref(false)
const pasteRecycleForm = reactive({
  recycle_reason: '',
  remark: ''
})
const pasteRecycleFormRef = ref()
const pasteEntries = computed(() => {
  if (!pasteIccidText.value.trim()) return []
  return [...new Set(
    pasteIccidText.value
      .split(/[\n,，\s]+/)
      .map(item => item.trim())
      .filter(Boolean)
  )]
})
const pasteIccids = computed(() => pasteEntries.value.filter(item => /^\d{10,}$/.test(item)))
const invalidPasteIccids = computed(() => pasteEntries.value.filter(item => !/^\d{10,}$/.test(item)))

// Excel批量回收
const uploadRef = ref()
const excelIccids = ref<{ iccid: string }[]>([])
const showExcelRecycleDialog = ref(false)
const excelRecycleForm = reactive({
  recycle_reason: '',
  remark: ''
})
const excelRecycleFormRef = ref()

// 回收记录
const recordParams = reactive({
  page: 1,
  page_size: 20
})
const recordDateRange = ref([])
const recycleRecords = ref<any[]>([])
const recordTotal = ref(0)
const recordsLoading = ref(false)

// 搜索卡片 - 使用 /cards API
const handleSearch = async () => {
  loading.value = true
  try {
    const params: any = {
      page: searchParams.page,
      page_size: searchParams.page_size
    }
    if (searchParams.keyword) params.keyword = searchParams.keyword
    if (searchParams.status) params.status = searchParams.status
    if (searchParams.carrier) params.carrier = searchParams.carrier

    const res: any = await cardApi.getList(params)
    outCards.value = res.items || res.list || []
    total.value = res.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    loading.value = false
  }
}

// 重置搜索
const handleResetSearch = () => {
  searchParams.keyword = ''
  searchParams.status = ''
  searchParams.carrier = ''
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

const openPasteRecycleDialog = () => {
  if (!pasteIccids.value.length) {
    ElMessage.warning('请粘贴需要回收的 ICCID')
    return
  }
  if (invalidPasteIccids.value.length) {
    ElMessage.warning('输入中包含无效 ICCID，请检查后再提交')
    return
  }
  if (pasteEntries.value.length > BATCH_RECYCLE_MAX_COUNT) {
    ElMessage.warning(`单次最多回收 ${BATCH_RECYCLE_MAX_COUNT} 张卡片`)
    return
  }
  showPasteRecycleDialog.value = true
}

const handlePasteRecycle = async () => {
  if (!pasteRecycleFormRef.value) return
  const valid = await pasteRecycleFormRef.value.validate().catch(() => false)
  if (!valid) return

  recycling.value = true
  try {
    const res = await stockApi.recycleByIccids({
      iccids: pasteIccids.value,
      recycle_reason: pasteRecycleForm.recycle_reason,
      remark: pasteRecycleForm.remark
    })
    const notFound = res.not_found || []
    const message = `回收完成！成功 ${res.success} 张，失败 ${res.failed} 张${
      notFound.length ? `；未找到：${notFound.slice(0, 5).join('、')}${notFound.length > 5 ? '…' : ''}` : ''
    }`

    ElMessage({
      message,
      type: res.failed > 0 ? 'warning' : 'success',
      duration: res.failed > 0 ? 8000 : 3000,
      showClose: res.failed > 0
    })

    showPasteRecycleDialog.value = false
    pasteRecycleForm.recycle_reason = ''
    pasteRecycleForm.remark = ''
    pasteIccidText.value = notFound.join('\n')

    if (res.success > 0) handleQueryRecords()
    if (res.failed === 0) activeTab.value = 'records'
  } catch (error: any) {
    ElMessage.error(error.message || '回收失败')
  } finally {
    recycling.value = false
  }
}

// 格式化流量
const formatFlow = (mb: number) => {
  if (!mb) return '-'
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(0)}GB`
  }
  return `${mb}MB`
}

// 格式化运营商
const formatCarrier = (carrier: string) => {
  const map: Record<string, string> = { cmcc: '移动', cucc: '联通', ctcc: '电信' }
  return map[carrier] || carrier
}

// 状态名称
const getStatusName = (status: string) => {
  const map: Record<string, string> = {
    stock: '库存', testing: '测试期', silent: '沉默期',
    activated: '已激活', expired: '已过期', suspended: '已停机', cancelled: '已注销'
  }
  return map[status] || status
}

// 状态标签类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    stock: 'info', testing: 'warning', silent: '',
    activated: 'success', expired: 'danger', suspended: 'danger', cancelled: 'info'
  }
  return map[status] || ''
}

// Excel文件解析
const handleFileChange = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target?.result as ArrayBuffer)
      const workbook = XLSX.read(data, { type: 'array' })
      const sheetName = workbook.SheetNames[0]
      if (!sheetName) {
        ElMessage.warning('Excel文件中未找到工作表')
        return
      }
      const sheet: any = workbook.Sheets[sheetName]
      const rows: any[] = XLSX.utils.sheet_to_json(sheet, { header: 1 })

      // 提取第一列的ICCID，跳过表头
      const iccids: { iccid: string }[] = []
      for (let i = 0; i < rows.length; i++) {
        const val = String(rows[i]?.[0] || '').trim()
        if (val && val.length >= 10 && /^\d+$/.test(val)) {
          iccids.push({ iccid: val })
        }
      }

      if (iccids.length === 0) {
        ElMessage.warning('未从Excel中解析到有效的ICCID')
        return
      }

      excelIccids.value = iccids
      ElMessage.success(`成功解析 ${iccids.length} 个ICCID`)
    } catch {
      ElMessage.error('Excel文件解析失败')
    }
  }
  reader.readAsArrayBuffer(file.raw)
}

const handleFileRemove = () => {
  excelIccids.value = []
}

// Excel批量回收
const handleExcelRecycle = async () => {
  if (!excelRecycleFormRef.value) return
  const valid = await excelRecycleFormRef.value.validate().catch(() => false)
  if (!valid) return

  recycling.value = true
  try {
    const iccids = excelIccids.value.map(item => item.iccid)
    const res = await stockApi.recycleByIccids({
      iccids,
      recycle_reason: excelRecycleForm.recycle_reason,
      remark: excelRecycleForm.remark
    })

    let msg = `回收完成！成功 ${res.success} 张，失败 ${res.failed} 张`
    if (res.not_found?.length > 0) {
      msg += `\n未找到: ${res.not_found.slice(0, 5).join(', ')}${res.not_found.length > 5 ? '...' : ''}`
    }
    ElMessage.success(msg)

    // 重置
    showExcelRecycleDialog.value = false
    excelRecycleForm.recycle_reason = ''
    excelRecycleForm.remark = ''
    excelIccids.value = []
    uploadRef.value?.clearFiles()

    activeTab.value = 'records'
    handleQueryRecords()
  } catch (error: any) {
    ElMessage.error(error.message || '回收失败')
  } finally {
    recycling.value = false
  }
}

onMounted(() => {
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

  .batch-input-info {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-top: 10px;
    color: #606266;
    font-size: 13px;

    .error-text {
      color: #f56c6c;
    }
  }
}
</style>
