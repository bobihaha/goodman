<template>
  <div class="suspend-policy-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>停卡策略管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增策略
          </el-button>
        </div>
      </template>

      <!-- 策略列表 -->
      <el-table :data="policyList" v-loading="loading" border>
        <el-table-column prop="name" label="策略名称" min-width="150" />
        <el-table-column prop="policy_type" label="策略类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getPolicyTypeTag(row.policy_type)">
              {{ getPolicyTypeName(row.policy_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="策略描述" min-width="200" />
        <el-table-column label="策略配置" min-width="250">
          <template #default="{ row }">
            <div v-if="row.policy_type === 'expired'">
              到期自动停卡
            </div>
            <div v-else-if="row.policy_type === 'pool_exceed'">
              告警: {{ row.warning_threshold }}% / 
              紧急: {{ row.critical_threshold }}% / 
              停卡: {{ row.stop_threshold }}%
            </div>
            <div v-else-if="row.policy_type === 'card_exceed'">
              告警: {{ row.warning_threshold }}% / 
              紧急: {{ row.critical_threshold }}% / 
              停卡: {{ row.stop_threshold }}%
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="is_enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="handleToggle(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑策略对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="策略名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入策略名称" />
        </el-form-item>

        <el-form-item label="策略类型" prop="policy_type">
          <el-select
            v-model="formData.policy_type"
            placeholder="请选择策略类型"
            :disabled="isEdit"
            style="width: 100%"
          >
            <el-option label="到期自动停卡" value="expired" />
            <el-option label="流量池超限停卡" value="pool_exceed" />
            <el-option label="单卡超量停卡" value="card_exceed" />
          </el-select>
        </el-form-item>

        <el-form-item label="策略描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入策略描述"
          />
        </el-form-item>

        <!-- 流量池/单卡超限配置 -->
        <template v-if="formData.policy_type === 'pool_exceed' || formData.policy_type === 'card_exceed'">
          <el-form-item label="告警阈值" prop="warning_threshold">
            <el-input-number
              v-model="formData.warning_threshold"
              :min="0"
              :max="100"
              placeholder="告警阈值"
            />
            <span class="form-tip">%（达到此使用率时发送告警）</span>
          </el-form-item>

          <el-form-item label="紧急阈值" prop="critical_threshold">
            <el-input-number
              v-model="formData.critical_threshold"
              :min="0"
              :max="100"
              placeholder="紧急阈值"
            />
            <span class="form-tip">%（达到此使用率时发送紧急告警）</span>
          </el-form-item>

          <el-form-item label="停卡阈值" prop="stop_threshold">
            <el-input-number
              v-model="formData.stop_threshold"
              :min="0"
              :max="100"
              placeholder="停卡阈值"
            />
            <span class="form-tip">%（达到此使用率时自动停卡）</span>
          </el-form-item>
        </template>

        <el-form-item label="自动停卡" prop="auto_suspend">
          <el-switch v-model="formData.auto_suspend" />
          <span class="form-tip">启用后达到阈值自动停卡</span>
        </el-form-item>

        <el-form-item label="启用状态" prop="is_enabled">
          <el-switch v-model="formData.is_enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getPolicies,
  createPolicy,
  updatePolicy,
  deletePolicy,
  type SuspendPolicy
} from '@/api/modules/suspend'

// 数据
const loading = ref(false)
const policyList = ref<SuspendPolicy[]>([])

// 对话框
const dialogVisible = ref(false)
const dialogTitle = computed(() => (isEdit.value ? '编辑策略' : '新增策略'))
const isEdit = ref(false)
const submitting = ref(false)

// 表单
const formRef = ref<FormInstance>()
const formData = reactive<Partial<SuspendPolicy>>({
  name: '',
  policy_type: 'expired',
  description: '',
  warning_threshold: 80,
  critical_threshold: 90,
  stop_threshold: 100,
  auto_suspend: true,
  auto_resume: false,
  notify_warning: true,
  notify_critical: true,
  notify_suspend: true,
  is_enabled: true
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入策略名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择策略类型', trigger: 'change' }],
  description: [{ required: true, message: '请输入策略描述', trigger: 'blur' }]
}

// 获取策略类型名称
const getPolicyTypeName = (type: string) => {
  const map: Record<string, string> = {
    expired: '到期停卡',
    pool_exceed: '流量池超限',
    card_exceed: '单卡超量'
  }
  return map[type] || type
}

// 获取策略类型标签
const getPolicyTypeTag = (type: string) => {
  const map: Record<string, any> = {
    expired: 'warning',
    pool_exceed: 'danger',
    card_exceed: 'danger'
  }
  return map[type] || 'info'
}

// 获取策略列表
const fetchPolicies = async () => {
  loading.value = true
  try {
    const res = await getPolicies({
      page: 1,
      page_size: 100
    })
    policyList.value = res.items || []
  } catch (error) {
    console.error('获取策略列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 新增策略
const handleCreate = () => {
  isEdit.value = false
  Object.assign(formData, {
    name: '',
    policy_type: 'expired',
    description: '',
    warning_threshold: 80,
    critical_threshold: 90,
    stop_threshold: 100,
    auto_suspend: true,
    auto_resume: false,
    notify_warning: true,
    notify_critical: true,
    notify_suspend: true,
    is_enabled: true
  })
  dialogVisible.value = true
}

// 编辑策略
const handleEdit = (row: SuspendPolicy) => {
  isEdit.value = true
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    policy_type: row.policy_type,
    description: row.description,
    warning_threshold: row.warning_threshold,
    critical_threshold: row.critical_threshold,
    stop_threshold: row.stop_threshold,
    auto_suspend: row.auto_suspend,
    auto_resume: row.auto_resume,
    notify_warning: row.notify_warning,
    notify_critical: row.notify_critical,
    notify_suspend: row.notify_suspend,
    is_enabled: row.is_enabled
  })
  dialogVisible.value = true
}

// 删除策略
const handleDelete = async (row: SuspendPolicy) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除策略"${row.name}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deletePolicy(row.id)
    ElMessage.success('删除成功')
    fetchPolicies()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除策略失败:', error)
    }
  }
}

// 切换策略状态
const handleToggle = async (row: SuspendPolicy) => {
  try {
    await updatePolicy(row.id, { is_enabled: row.is_enabled })
    ElMessage.success(row.is_enabled ? '已启用' : '已禁用')
  } catch (error) {
    console.error('切换状态失败:', error)
    row.is_enabled = !row.is_enabled
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value && formData.id) {
      await updatePolicy(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await createPolicy(formData)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    fetchPolicies()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
const handleDialogClose = () => {
  formRef.value?.resetFields()
}

// 初始化
onMounted(() => {
  fetchPolicies()
})
</script>

<style scoped lang="scss">
.suspend-policy-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
