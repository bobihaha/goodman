<template>
  <div class="stock-in-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">卡片入库</span>
        </div>
      </template>

      <el-steps :active="currentStep" finish-status="success" align-center class="steps">
        <el-step title="导入卡片" />
        <el-step title="确认入库" />
      </el-steps>

      <!-- 步骤1: 导入卡片 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="import-section">
          <!-- 入库基本信息 -->
          <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px" style="max-width: 700px; margin: 0 auto 30px">
            <el-form-item label="供应商" prop="supplier_id">
              <el-select v-model="formData.supplier_id" placeholder="请选择供应商" filterable style="width: 100%">
                <el-option
                  v-for="supplier in suppliers"
                  :key="supplier.id"
                  :label="supplier.name"
                  :value="supplier.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="底层套餐" prop="package_id">
              <el-select v-model="formData.package_id" placeholder="请选择底层套餐" filterable style="width: 100%">
                <el-option
                  v-for="pkg in supplierPackages"
                  :key="pkg.id"
                  :label="`${pkg.name} - ${pkg.carrier_name}/${formatFlow(pkg.flow_size)}/${pkg.period_name}`"
                  :value="pkg.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="测试期截止日期">
              <el-date-picker
                v-model="formData.test_expire_date"
                type="date"
                placeholder="选择测试期截止日期（可选）"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="沉默期截止日期" prop="silent_expire_date">
              <el-date-picker
                v-model="formData.silent_expire_date"
                type="date"
                placeholder="选择沉默期截止日期（必填）"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="formData.remark" type="textarea" :rows="3" placeholder="请输入备注（可选）" />
            </el-form-item>
          </el-form>

          <el-divider />

          <!-- Excel导入说明 -->
          <el-alert
            title="Excel导入说明"
            type="info"
            :closable="false"
            style="margin-bottom: 20px; max-width: 700px; margin-left: auto; margin-right: auto"
          >
            <div>1. 请使用固定模板格式：列A-ICCID（必填）、列B-IMSI（必填）、列C-电话号码（必填）</div>
            <div>2. 支持 Excel (.xlsx, .xls) 和 CSV 格式</div>
            <div>3. 第一行为表头，从第二行开始为数据</div>
            <div>4. 单次最多导入 10000 条</div>
          </el-alert>

          <div style="max-width: 700px; margin: 0 auto 20px; text-align: center">
            <el-button type="success" @click="handleDownloadTemplate">
              <el-icon><Download /></el-icon>
              下载Excel模板
            </el-button>
          </div>

          <div class="upload-area">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :on-change="handleFileChange"
              :limit="1"
              accept=".xlsx,.xls,.csv"
              drag
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 .xlsx, .xls, .csv 格式，单次最多导入 10000 条
                </div>
              </template>
            </el-upload>
          </div>

          <!-- 手动输入 -->
          <el-divider>或手动输入</el-divider>
          <el-form :model="manualForm" label-width="100px" style="max-width: 600px; margin: 0 auto">
            <el-form-item label="ICCID" required>
              <el-input v-model="manualForm.iccid" placeholder="请输入ICCID（19-20位字母或数字）" maxlength="20" />
            </el-form-item>
            <el-form-item label="IMSI" required>
              <el-input v-model="manualForm.imsi" placeholder="请输入IMSI（15位数字）" maxlength="15" />
            </el-form-item>
            <el-form-item label="电话号码" required>
              <el-input v-model="manualForm.msisdn" placeholder="请输入电话号码（1-20位数字）" maxlength="20" />
            </el-form-item>
            <el-form-item>
              <el-button @click="handleAddCard">添加到列表</el-button>
            </el-form-item>
          </el-form>

          <!-- 卡片列表 -->
          <div v-if="cardList.length > 0" class="card-list">
            <div class="list-header">
              <span>已添加 {{ cardList.length }} 张卡片</span>
              <el-button size="small" @click="handleClearList">清空列表</el-button>
            </div>
            <el-table :data="cardList" border stripe max-height="300">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="iccid" label="ICCID" />
              <el-table-column prop="imsi" label="IMSI" />
              <el-table-column prop="msisdn" label="MSISDN" />
              <el-table-column label="操作" width="80">
                <template #default="{ $index }">
                  <el-button link type="danger" size="small" @click="handleRemoveCard($index)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div class="step-actions">
            <el-button type="primary" @click="nextStep" :disabled="cardList.length === 0">
              下一步
            </el-button>
          </div>
        </div>
      </div>

      <!-- 步骤2: 确认入库 -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="confirm-section">
          <el-descriptions title="入库信息" :column="2" border>
            <el-descriptions-item label="供应商">
              {{ selectedSupplier?.name || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="底层套餐">
              {{ selectedPackage?.name || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="测试期截止日期">
              {{ formData.test_expire_date || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="沉默期截止日期">
              {{ formData.silent_expire_date || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="卡片数量">
              <el-tag type="success">{{ cardList.length }} 张</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">
              {{ formData.remark || '-' }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 卡片列表预览 -->
          <div class="card-list-preview">
            <div class="list-title">入库卡片列表</div>
            <el-table :data="cardList" border stripe max-height="400">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="iccid" label="ICCID" />
              <el-table-column prop="imsi" label="IMSI" />
              <el-table-column prop="msisdn" label="MSISDN" />
            </el-table>
          </div>

          <div class="step-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="submitting">
              确认入库
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Download } from '@element-plus/icons-vue'
import { stockApi } from '@/api/modules/stock'
import { supplierApi } from '@/api/modules/supplier'
import { packageApi } from '@/api/modules/package'
import * as XLSX from 'xlsx'

// 当前步骤
const currentStep = ref(0)

// 表单数据
const formData = reactive({
  supplier_id: undefined as number | undefined,
  package_id: undefined as number | undefined,
  test_expire_date: '',
  silent_expire_date: '',
  remark: ''
})

// 表单验证规则
const formRules = {
  supplier_id: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  package_id: [{ required: true, message: '请选择底层套餐', trigger: 'change' }],
  silent_expire_date: [{ required: true, message: '请选择沉默期截止日期', trigger: 'change' }]
}

const formRef = ref()

// 手动输入表单
const manualForm = reactive({
  iccid: '',
  imsi: '',
  msisdn: ''
})

// 卡片列表
const cardList = ref<any[]>([])

// 供应商、套餐列表
const suppliers = ref<any[]>([])
const supplierPackages = ref<any[]>([])

// 上传组件引用
const uploadRef = ref()

// 提交状态
const submitting = ref(false)

// 选中的供应商
const selectedSupplier = computed(() => {
  return suppliers.value.find((s: any) => s.id === formData.supplier_id)
})

// 选中的套餐
const selectedPackage = computed(() => {
  return supplierPackages.value.find((p: any) => p.id === formData.package_id)
})

// 获取供应商列表
const fetchSuppliers = async () => {
  try {
    const res = await supplierApi.getList({ page: 1, page_size: 100 })
    suppliers.value = res.list || res.data?.items || res.data?.list || []
  } catch (error) {
    console.error('获取供应商列表失败', error)
  }
}

// 获取底层套餐列表
const fetchSupplierPackages = async () => {
  try {
    const res = await packageApi.getSupplierPackages({ page: 1, page_size: 100 })
    supplierPackages.value = res.list || res.data?.items || res.data?.list || []
  } catch (error) {
    console.error('获取底层套餐列表失败', error)
  }
}

// 下一步
const nextStep = async () => {
  if (currentStep.value === 0) {
    // 验证表单
    if (!formRef.value) return
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
    
    // 验证卡片列表
    if (cardList.value.length === 0) {
      ElMessage.warning('请至少添加一张卡片')
      return
    }
  }
  
  if (currentStep.value < 1) {
    currentStep.value++
  }
}

// 下载Excel模板
const handleDownloadTemplate = () => {
  // 创建模板数据
  const templateData = [
    ['ICCID', 'IMSI', '电话号码'],
    ['89860123456789012345', '460012345678901', '13800138000'],
    ['89860123456789012346', '460012345678902', '13800138001']
  ]
  
  // 创建工作簿
  const ws = XLSX.utils.aoa_to_sheet(templateData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '卡片导入模板')
  
  // 下载文件
  XLSX.writeFile(wb, '卡片入库导入模板.xlsx')
  ElMessage.success('模板下载成功')
}

// 格式化流量
const formatFlow = (mb: number) => {
  if (!mb) return '-'
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(0)}GB`
  }
  return `${mb}MB`
}

// 上一步
const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const normalizeExcelCell = (value: unknown) => {
  const text = String(value ?? '').trim()
  return text.replace(/\.0+$/, '')
}

// 处理文件变化
const handleFileChange = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e: any) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      const rows = XLSX.utils.sheet_to_json(firstSheet, {
        header: 1,
        raw: false,
        defval: ''
      }) as any[][]
      
      // 解析数据
      const cards: any[] = []
      const errors: string[] = []

      if (rows.length <= 1) {
        ElMessage.warning('未找到有效的卡片数据')
        return
      }

      rows.slice(1).forEach((row: any[], index: number) => {
        const iccid = normalizeExcelCell(row?.[0])
        const imsi = normalizeExcelCell(row?.[1])
        const msisdn = normalizeExcelCell(row?.[2])

        // 跳过完全空白行
        if (!iccid && !imsi && !msisdn) {
          return
        }
        
        // 验证必填字段
        if (!iccid) {
          errors.push(`第${index + 2}行：ICCID不能为空`)
          return
        }
        if (!imsi) {
          errors.push(`第${index + 2}行：IMSI不能为空`)
          return
        }
        if (!msisdn) {
          errors.push(`第${index + 2}行：电话号码不能为空`)
          return
        }
        
        // 验证格式
        if (!/^[0-9A-Za-z]{19,20}$/.test(iccid)) {
          errors.push(`第${index + 2}行：ICCID格式错误（应为19-20位字母或数字）`)
          return
        }
        // 电话号码仅做基础校验，兼容不同供应商的号码长度
        if (!/^\d{1,20}$/.test(msisdn)) {
          errors.push(`第${index + 2}行：电话号码格式错误（应为1-20位数字）`)
          return
        }
        
        cards.push({ iccid, imsi, msisdn })
      })
      
      if (errors.length > 0) {
        ElMessage.error({
          message: `导入失败，发现 ${errors.length} 个错误：\n${errors.slice(0, 5).join('\n')}${errors.length > 5 ? '\n...' : ''}`,
          duration: 5000
        })
        return
      }
      
      if (cards.length === 0) {
        ElMessage.warning('未找到有效的卡片数据')
        return
      }
      
      if (cards.length > 10000) {
        ElMessage.warning('单次最多导入10000条数据')
        return
      }
      
      cardList.value = cards
      ElMessage.success(`成功导入 ${cards.length} 张卡片`)
    } catch (error) {
      console.error('文件解析失败', error)
      ElMessage.error('文件解析失败，请检查文件格式')
    }
  }
  reader.readAsArrayBuffer(file.raw)
}

// 添加卡片
const handleAddCard = () => {
  // 验证必填字段
  if (!manualForm.iccid) {
    ElMessage.warning('请输入ICCID')
    return
  }
  if (!manualForm.imsi) {
    ElMessage.warning('请输入IMSI')
    return
  }
  if (!manualForm.msisdn) {
    ElMessage.warning('请输入电话号码')
    return
  }
  
  // 验证格式
  if (!/^[0-9A-Za-z]{19,20}$/.test(manualForm.iccid)) {
    ElMessage.warning('ICCID格式错误（应为19-20位字母或数字）')
    return
  }
  // 电话号码仅做基础校验，兼容不同供应商的号码长度
  if (!/^\d{1,20}$/.test(manualForm.msisdn)) {
    ElMessage.warning('电话号码格式错误（应为1-20位数字）')
    return
  }
  
  // 检查是否重复
  if (cardList.value.some(card => card.iccid === manualForm.iccid)) {
    ElMessage.warning('该ICCID已存在')
    return
  }
  
  cardList.value.push({
    iccid: manualForm.iccid,
    imsi: manualForm.imsi,
    msisdn: manualForm.msisdn
  })
  
  // 清空表单
  manualForm.iccid = ''
  manualForm.imsi = ''
  manualForm.msisdn = ''
  
  ElMessage.success('添加成功')
}

// 移除卡片
const handleRemoveCard = (index: number) => {
  cardList.value.splice(index, 1)
}

// 清空列表
const handleClearList = () => {
  cardList.value = []
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 提交入库
const handleSubmit = async () => {
  submitting.value = true
  try {
    // 步骤1：先创建批次
    const batch = await stockApi.createBatch({
      supplier_id: formData.supplier_id!,
      package_id: formData.package_id!,
      test_expire_date: formData.test_expire_date || undefined,
      silent_expire_date: formData.silent_expire_date,
      purchase_date: new Date().toISOString().split('T')[0], // 当前日期
      remark: formData.remark
    })
    
    // 响应拦截器已经解包，直接使用 batch.id
    const batchId = batch.id
    
    // 步骤2：使用批次ID进行入库
    const result = await stockApi.stockIn({
      batch_id: batchId,
      cards: cardList.value,
      remark: formData.remark
    })
    
    ElMessage.success(`入库成功！成功 ${result.success} 张，失败 ${result.failed} 张`)
    
    // 重置表单
    cardList.value = []
    formData.supplier_id = undefined
    formData.package_id = undefined
    formData.test_expire_date = ''
    formData.silent_expire_date = ''
    formData.remark = ''
    currentStep.value = 0
    
    if (uploadRef.value) {
      uploadRef.value.clearFiles()
    }
  } catch (error: any) {
    ElMessage.error(error.message || '入库失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchSuppliers()
  fetchSupplierPackages()
})
</script>

<style scoped lang="scss">
.stock-in-container {
  padding: 20px;

  .card-header {
    .title {
      font-size: 16px;
      font-weight: 600;
    }
  }

  .steps {
    margin: 30px 0;
  }

  .step-content {
    min-height: 400px;
    padding: 20px 0;
  }

  .import-section {
    max-width: 800px;
    margin: 0 auto;

    .upload-area {
      margin: 20px 0;
    }

    .card-list {
      margin-top: 30px;

      .list-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-weight: 600;
      }
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
</style>
