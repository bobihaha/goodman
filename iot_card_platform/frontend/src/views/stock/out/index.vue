<template>
  <div class="stock-out-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">卡片出库</span>
          <div class="header-actions">
            <el-button type="success" @click="showBatchImportDialog = true">
              <el-icon><Upload /></el-icon>
              Excel批量出库
            </el-button>
          </div>
        </div>
      </template>

      <el-steps :active="currentStep" finish-status="success" align-center class="steps">
        <el-step title="选择卡片" />
        <el-step title="选择用户和套餐" />
        <el-step title="确认出库" />
      </el-steps>

      <!-- 步骤1: 选择卡片 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="select-cards-section">
          <!-- 搜索栏 -->
          <el-form :inline="true" :model="queryParams" class="search-form">
            <el-form-item label="供应商">
              <el-select v-model="queryParams.supplier_id" placeholder="请选择" clearable style="width: 150px">
                <el-option
                  v-for="supplier in suppliers"
                  :key="supplier.id"
                  :label="supplier.name"
                  :value="supplier.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="运营商">
              <el-select v-model="queryParams.carrier" placeholder="请选择" clearable style="width: 120px">
                <el-option label="中国移动" value="cmcc" />
                <el-option label="中国联通" value="cucc" />
                <el-option label="中国电信" value="ctcc" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleQuery">查询</el-button>
              <el-button @click="handleReset">重置</el-button>
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

          <!-- 表格 -->
          <el-table
            :data="tableData"
            v-loading="loading"
            border
            stripe
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="iccid" label="ICCID" width="200" />
            <el-table-column prop="imsi" label="IMSI" width="150" />
            <el-table-column prop="msisdn" label="MSISDN" width="130" />
            <el-table-column prop="supplier_name" label="供应商" width="120" />
            <el-table-column label="规格" width="200">
              <template #default="{ row }">
                {{ row.carrier_name }} / {{ formatFlow(row.flow_size) }} / {{ row.period_name }}
              </template>
            </el-table-column>
            <el-table-column label="生命周期" width="180">
              <template #default="{ row }">
                <div style="font-size: 12px">
                  <div v-if="row.test_expire_date">测试: {{ row.test_expire_date }}</div>
                  <div>沉默: {{ row.silent_expire_date }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="stock_in_at" label="入库时间" width="160" />
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

          <div class="step-actions">
            <el-button type="primary" @click="nextStep" :disabled="selectedCards.length === 0">
              下一步（已选 {{ selectedCards.length }} 张）
            </el-button>
          </div>
        </div>
      </div>

      <!-- 步骤2: 选择用户和套餐 -->
      <div v-if="currentStep === 1" class="step-content">
        <el-form :model="outForm" :rules="rules" ref="formRef" label-width="140px" style="max-width: 700px; margin: 40px auto">
          <el-form-item label="目标用户" prop="to_user_id">
            <el-select v-model="outForm.to_user_id" placeholder="请选择目标用户" filterable style="width: 100%">
              <el-option
                v-for="user in users"
                :key="user.id"
                :label="`${user.name} (${user.account})`"
                :value="user.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="销售套餐" prop="sale_package_id">
            <el-select 
              v-model="outForm.sale_package_id" 
              placeholder="请选择销售套餐" 
              filterable 
              style="width: 100%"
              @change="handlePackageChange"
            >
              <el-option
                v-for="pkg in salePackages"
                :key="pkg.id"
                :label="`${pkg.name} - ${pkg.carrier_name}/${formatFlow(pkg.flow_size)}/${pkg.period_name} - ¥${pkg.price_sale}`"
                :value="pkg.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="套餐周期" prop="period_count">
            <el-select v-model="outForm.period_count" placeholder="请选择套餐周期" style="width: 100%">
              <el-option
                v-for="period in periodOptions"
                :key="period.value"
                :label="period.label"
                :value="period.value"
              />
            </el-select>
            <div style="color: #909399; font-size: 12px; margin-top: 5px">
              {{ selectedPackagePeriodType === 'yearly' ? '注意：年包有效期为360天/年' : '' }}
            </div>
          </el-form-item>

          <el-form-item 
            v-if="selectedPackagePeriodType === 'monthly'" 
            label="卡类型" 
            prop="card_type"
          >
            <el-radio-group v-model="outForm.card_type">
              <el-radio label="single">单卡（达量停机）</el-radio>
              <el-radio label="pool">流量池卡（共享流量）</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="出库日期" prop="stock_out_date">
            <el-date-picker
              v-model="outForm.stock_out_date"
              type="date"
              placeholder="选择出库日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="测试期截止日期">
            <el-date-picker
              v-model="outForm.test_expire_date"
              type="date"
              placeholder="选择测试期截止日期（可选）"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="沉默期截止日期" prop="silent_expire_date">
            <el-date-picker
              v-model="outForm.silent_expire_date"
              type="date"
              placeholder="选择沉默期截止日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          
          <el-form-item label="备注">
            <el-input v-model="outForm.remark" type="textarea" :rows="3" placeholder="请输入备注" />
          </el-form-item>
        </el-form>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="primary" @click="nextStep">下一步</el-button>
        </div>
      </div>

      <!-- 步骤3: 确认出库 -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="confirm-section">
          <el-descriptions title="出库信息" :column="2" border>
            <el-descriptions-item label="目标用户">
              {{ selectedUser?.name }} ({{ selectedUser?.account }})
            </el-descriptions-item>
            <el-descriptions-item label="销售套餐">
              {{ selectedPackage?.name }}
            </el-descriptions-item>
            <el-descriptions-item label="套餐周期">
              <el-tag type="primary">
                {{ outForm.period_count }} {{ selectedPackagePeriodType === 'yearly' ? '年' : '个月' }}
              </el-tag>
              <span v-if="selectedPackagePeriodType === 'yearly'" style="color: #909399; font-size: 12px; margin-left: 10px">
                (有效期: {{ outForm.period_count * 360 }} 天)
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="卡类型" v-if="selectedPackagePeriodType === 'monthly'">
              <el-tag :type="outForm.card_type === 'single' ? 'warning' : 'success'">
                {{ outForm.card_type === 'single' ? '单卡（达量停机）' : '流量池卡（共享流量）' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="出库日期">
              {{ outForm.stock_out_date }}
            </el-descriptions-item>
            <el-descriptions-item label="测试期截止日期">
              {{ outForm.test_expire_date || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="沉默期截止日期">
              {{ outForm.silent_expire_date }}
            </el-descriptions-item>
            <el-descriptions-item label="套餐价格">
              ¥{{ selectedPackage?.price_sale }}
            </el-descriptions-item>
            <el-descriptions-item label="卡片数量">
              <el-tag type="success">{{ selectedCards.length }} 张</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="总金额">
              <el-tag type="danger" size="large">
                ¥{{ (selectedCards.length * (selectedPackage?.price_sale || 0)).toFixed(2) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">
              {{ outForm.remark || '-' }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 卡片列表 -->
          <div class="card-list-preview">
            <div class="list-title">出库卡片列表</div>
            <el-table :data="selectedCards" border stripe max-height="300">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="iccid" label="ICCID" />
              <el-table-column prop="imsi" label="IMSI" />
              <el-table-column prop="msisdn" label="MSISDN" />
              <el-table-column prop="supplier_name" label="供应商" />
            </el-table>
          </div>

          <div class="step-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="submitting">
              确认出库
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Excel批量出库对话框 -->
    <el-dialog
      v-model="showBatchImportDialog"
      title="Excel批量出库"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="batch-import-content">
        <el-alert
          title="使用说明"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        >
          <div style="font-size: 13px; line-height: 1.8">
            <div>1. 下载Excel模板，按照模板格式填写数据</div>
            <div>2. 月包套餐必须填写卡类型（single/pool），年包可不填</div>
            <div>3. 套餐周期：月包填月数（3/6/12等），年包填年数（1/2/3等）</div>
            <div>4. 年包有效期为360天/年，不是365天</div>
            <div>5. 日期格式：YYYY-MM-DD（如：2026-02-11）</div>
          </div>
        </el-alert>

        <div class="template-download">
          <el-button type="primary" @click="downloadTemplate" :loading="downloadingTemplate">
            <el-icon><Download /></el-icon>
            下载Excel模板
          </el-button>
        </div>

        <el-divider />

        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
          drag
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将Excel文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              只能上传 xlsx/xls 文件
            </div>
          </template>
        </el-upload>

        <div v-if="importResult" class="import-result">
          <el-alert
            :title="`导入完成：成功 ${importResult.success} 条，失败 ${importResult.failed} 条`"
            :type="importResult.failed > 0 ? 'warning' : 'success'"
            :closable="false"
          />
          
          <div v-if="importResult.fail_details && importResult.fail_details.length > 0" class="fail-details">
            <div class="fail-title">失败详情：</div>
            <el-table :data="importResult.fail_details" border stripe max-height="200">
              <el-table-column prop="row" label="行号" width="80" />
              <el-table-column prop="iccid" label="ICCID" width="180" />
              <el-table-column prop="reason" label="失败原因" />
            </el-table>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showBatchImportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBatchImport" :loading="importing" :disabled="!selectedFile">
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Download, UploadFilled } from '@element-plus/icons-vue'
import { stockApi } from '@/api/modules/stock'
import { supplierApi } from '@/api/modules/supplier'
import { packageApi } from '@/api/modules/package'
import { userApi } from '@/api/modules/user'
import { useRouter } from 'vue-router'
import * as XLSX from 'xlsx'

const router = useRouter()

// 当前步骤
const currentStep = ref(0)

// 查询参数
const queryParams = reactive({
  supplier_id: undefined,
  carrier: undefined,
  page: 1,
  page_size: 20
})

// 表格数据
const tableData = ref([])
const total = ref(0)
const loading = ref(false)

// 选中的卡片
const selectedCards = ref<any[]>([])

// 供应商、用户、套餐列表
const suppliers = ref([])
const users = ref([])
const salePackages = ref([])

// 出库表单
const outForm = reactive({
  to_user_id: undefined as number | undefined,
  sale_package_id: undefined as number | undefined,
  period_count: undefined as number | undefined,
  card_type: 'single' as 'single' | 'pool',
  stock_out_date: '',
  test_expire_date: '',
  silent_expire_date: '',
  remark: ''
})

const formRef = ref()
const submitting = ref(false)

// 表单验证规则
const rules = {
  to_user_id: [{ required: true, message: '请选择目标用户', trigger: 'change' }],
  sale_package_id: [{ required: true, message: '请选择销售套餐', trigger: 'change' }],
  period_count: [{ required: true, message: '请选择套餐周期', trigger: 'change' }],
  card_type: [{ required: true, message: '请选择卡类型', trigger: 'change' }],
  stock_out_date: [{ required: true, message: '请选择出库日期', trigger: 'change' }],
  silent_expire_date: [{ required: true, message: '请选择沉默期截止日期', trigger: 'change' }]
}

// 月包套餐周期选项
const monthlyPeriods = [
  { label: '3个月', value: 3 },
  { label: '6个月', value: 6 },
  { label: '12个月', value: 12 },
  { label: '24个月', value: 24 },
  { label: '36个月', value: 36 },
  { label: '50个月', value: 50 },
  { label: '60个月', value: 60 }
]

// 年包套餐周期选项
const yearlyPeriods = [
  { label: '1年', value: 1 },
  { label: '2年', value: 2 },
  { label: '3年', value: 3 },
  { label: '5年', value: 5 },
  { label: '6年', value: 6 }
]

// 选中的套餐周期类型
const selectedPackagePeriodType = computed(() => {
  const pkg = salePackages.value.find((p: any) => p.id === outForm.sale_package_id)
  return pkg?.period_type || 'monthly'
})

// 动态套餐周期选项
const periodOptions = computed(() => {
  return selectedPackagePeriodType.value === 'yearly' ? yearlyPeriods : monthlyPeriods
})

// 选中的用户
const selectedUser = computed(() => {
  return users.value.find((u: any) => u.id === outForm.to_user_id)
})

// 选中的套餐
const selectedPackage = computed(() => {
  return salePackages.value.find((p: any) => p.id === outForm.sale_package_id)
})

// 获取库存卡片
const fetchInventory = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory(queryParams)
    tableData.value = res.items || []  // 库存API返回 items
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('获取库存卡片失败')
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

// 获取用户列表
const fetchUsers = async () => {
  try {
    const res = await userApi.getList({ page: 1, page_size: 100 })
    users.value = (res.list || res.data?.items || res.data?.list || []).filter((u: any) => u.user_level === 2) // 只显示普通用户
  } catch (error) {
    console.error('获取用户列表失败', error)
  }
}

// 获取销售套餐列表
const fetchSalePackages = async () => {
  try {
    const res = await packageApi.getSalePackages({ page: 1, page_size: 100, status: 'enable' })
    salePackages.value = res.list || []  // 销售套餐API返回 list
  } catch (error) {
    console.error('获取销售套餐列表失败', error)
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
  queryParams.page = 1
  fetchInventory()
}

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedCards.value = selection
}

// 套餐变化处理
const handlePackageChange = () => {
  // 重置套餐周期
  outForm.period_count = undefined
  // 如果是年包，重置卡类型为单卡
  if (selectedPackagePeriodType.value === 'yearly') {
    outForm.card_type = 'single'
  }
}

// 下一步
const nextStep = async () => {
  if (currentStep.value === 1) {
    // 验证表单
    if (!formRef.value) return
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
  }
  
  if (currentStep.value < 2) {
    currentStep.value++
  }
}

// 上一步
const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// 提交出库
const handleSubmit = async () => {
  submitting.value = true
  try {
    const card_ids = selectedCards.value.map(card => card.id)
    
    // 构建请求数据
    const requestData: any = {
      card_ids,
      to_user_id: outForm.to_user_id!,
      sale_package_id: outForm.sale_package_id!,
      period_count: outForm.period_count!,
      stock_out_date: outForm.stock_out_date,
      silent_expire_date: outForm.silent_expire_date,
      remark: outForm.remark
    }
    
    // 月包需要卡类型
    if (selectedPackagePeriodType.value === 'monthly') {
      requestData.card_type = outForm.card_type
    }
    
    // 测试期（可选）
    if (outForm.test_expire_date) {
      requestData.test_expire_date = outForm.test_expire_date
    }
    
    const res = await stockApi.stockOut(requestData)
    
    ElMessage.success(`出库成功！成功 ${res.success} 张，失败 ${res.failed} 张`)
    
    // 跳转到出库记录
    router.push('/stock/records')
  } catch (error: any) {
    ElMessage.error(error.message || '出库失败')
  } finally {
    submitting.value = false
  }
}

// 格式化流量
const formatFlow = (mb: number) => {
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(0)}GB`
  }
  return `${mb}MB`
}

// ============ Excel批量出库 ============

const showBatchImportDialog = ref(false)
const uploadRef = ref()
const selectedFile = ref<File | null>(null)
const importing = ref(false)
const downloadingTemplate = ref(false)
const importResult = ref<any>(null)

// 下载Excel模板
const downloadTemplate = async () => {
  downloadingTemplate.value = true
  try {
    const res = await stockApi.downloadStockOutTemplate()
    
    // 创建工作簿
    const ws = XLSX.utils.aoa_to_sheet(res)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '出库模板')
    
    // 下载文件
    XLSX.writeFile(wb, '出库模板.xlsx')
    ElMessage.success('模板下载成功')
  } catch (error) {
    ElMessage.error('模板下载失败')
  } finally {
    downloadingTemplate.value = false
  }
}

// 文件选择变化
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
  importResult.value = null
}

// 文件超出限制
const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

// 批量导入
const handleBatchImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  importing.value = true
  importResult.value = null

  try {
    // 读取Excel文件
    const data = await selectedFile.value.arrayBuffer()
    const workbook = XLSX.read(data)
    const worksheet = workbook.Sheets[workbook.SheetNames[0]]
    const jsonData: any[] = XLSX.utils.sheet_to_json(worksheet, { header: 1 })

    // 跳过表头，转换数据
    const items = jsonData.slice(1).map((row: any) => ({
      iccid: row[0],
      user_id: parseInt(row[1]),
      sale_package_id: parseInt(row[2]),
      period_count: parseInt(row[3]),
      card_type: row[4] || null,
      stock_out_date: row[5],
      test_expire_date: row[6] || null,
      silent_expire_date: row[7],
      remark: row[8] || null
    })).filter((item: any) => item.iccid) // 过滤空行

    if (items.length === 0) {
      ElMessage.warning('Excel文件中没有有效数据')
      return
    }

    // 调用批量出库API
    const result = await stockApi.batchStockOutImport({ items })
    
    importResult.value = result
    
    if (result.failed === 0) {
      ElMessage.success(`批量出库成功！共 ${result.success} 张卡片`)
      // 清空文件
      selectedFile.value = null
      if (uploadRef.value) {
        uploadRef.value.clearFiles()
      }
    } else {
      ElMessage.warning(`批量出库完成：成功 ${result.success} 张，失败 ${result.failed} 张`)
    }
  } catch (error: any) {
    ElMessage.error(error.message || '批量导入失败')
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  fetchInventory()
  fetchSuppliers()
  fetchUsers()
  fetchSalePackages()
})
</script>

<style scoped lang="scss">
.stock-out-container {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      font-size: 16px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .steps {
    margin: 30px 0;
  }

  .step-content {
    min-height: 400px;
    padding: 20px 0;
  }

  .select-cards-section {
    .search-form {
      margin-bottom: 20px;
    }

    .pagination {
      margin-top: 20px;
      justify-content: flex-end;
    }
  }

  .confirm-section {
    max-width: 900px;
    margin: 40px auto;

    .card-list-preview {
      margin-top: 30px;

      .list-title {
        font-weight: 600;
        margin-bottom: 10px;
      }
    }
  }

  .step-actions {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 40px;
  }
}

.batch-import-content {
  .template-download {
    text-align: center;
    margin: 20px 0;
  }

  .import-result {
    margin-top: 20px;

    .fail-details {
      margin-top: 15px;

      .fail-title {
        font-weight: 600;
        margin-bottom: 10px;
        color: #e6a23c;
      }
    }
  }
}
</style>

