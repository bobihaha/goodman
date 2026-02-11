<template>
  <el-dialog
    v-model="visible"
    title="添加卡片到流量池"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-alert
      v-if="pool"
      :title="`流量池：${pool.name} | 运营商：${CARRIER_MAP[pool.carrier]} | 规格：${formatFlow(pool.flow_size)}/${PERIOD_TYPE_MAP[pool.period_type]}`"
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    />

    <el-form ref="formRef" :model="formData" :rules="rules">
      <el-form-item label="输入方式">
        <el-radio-group v-model="inputMode">
          <el-radio label="iccid">输入ICCID</el-radio>
          <el-radio label="select">选择卡片</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="inputMode === 'iccid'" label="ICCID列表" prop="iccids">
        <el-input
          v-model="iccidText"
          type="textarea"
          :rows="10"
          placeholder="请输入ICCID，每行一个或用逗号分隔，最多1000个"
        />
        <div class="form-tip">
          已输入 {{ iccidCount }} 个ICCID
          <span v-if="iccidCount > 1000" style="color: #f56c6c">（超出限制）</span>
        </div>
      </el-form-item>

      <el-form-item v-else label="选择卡片" prop="card_ids">
        <el-button type="primary" @click="handleSelectCards">
          选择卡片（已选 {{ selectedCards.length }} 张）
        </el-button>
        <div v-if="selectedCards.length > 0" class="selected-cards">
          <el-tag
            v-for="card in selectedCards.slice(0, 10)"
            :key="card.id"
            closable
            @close="handleRemoveCard(card.id)"
          >
            {{ card.iccid }}
          </el-tag>
          <span v-if="selectedCards.length > 10">
            等 {{ selectedCards.length }} 张卡片
          </span>
        </div>
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入备注信息（可选）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        确定添加
      </el-button>
    </template>

    <!-- 卡片选择对话框 -->
    <CardSelectDialog
      v-model="cardSelectVisible"
      :pool="pool"
      :selected-cards="selectedCards"
      @confirm="handleCardsSelected"
    />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { addCardsToPool } from '@/api/modules/pool'
import { formatFlow } from '@/utils/formatter'
import { CARRIER_MAP, PERIOD_TYPE_MAP } from '@/constants/card'
import type { Pool } from '@/types/pool'
import CardSelectDialog from './CardSelectDialog.vue'

interface Props {
  modelValue: boolean
  pool?: Pool | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const cardSelectVisible = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 输入模式
const inputMode = ref<'iccid' | 'select'>('iccid')

// ICCID文本输入
const iccidText = ref('')

// 已选择的卡片
const selectedCards = ref<any[]>([])

// 表单数据
const formData = reactive({
  iccids: [] as string[],
  card_ids: [] as number[],
  remark: ''
})

// ICCID数量
const iccidCount = computed(() => {
  if (!iccidText.value.trim()) return 0
  const iccids = iccidText.value
    .split(/[\n,，]/)
    .map(s => s.trim())
    .filter(s => s.length > 0)
  return iccids.length
})

// 表单验证规则
const rules: FormRules = {
  iccids: [
    {
      validator: (rule, value, callback) => {
        if (inputMode.value === 'iccid') {
          if (!iccidText.value.trim()) {
            callback(new Error('请输入ICCID'))
          } else if (iccidCount.value > 1000) {
            callback(new Error('ICCID数量不能超过1000个'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  card_ids: [
    {
      validator: (rule, value, callback) => {
        if (inputMode.value === 'select' && selectedCards.value.length === 0) {
          callback(new Error('请选择卡片'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

/**
 * 打开卡片选择对话框
 */
const handleSelectCards = () => {
  cardSelectVisible.value = true
}

/**
 * 卡片选择完成
 */
const handleCardsSelected = (cards: any[]) => {
  selectedCards.value = cards
}

/**
 * 移除已选卡片
 */
const handleRemoveCard = (cardId: number) => {
  selectedCards.value = selectedCards.value.filter(c => c.id !== cardId)
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!formRef.value || !props.pool) return

  try {
    await formRef.value.validate()
    submitting.value = true

    // 准备请求数据
    const requestData: any = {
      pool_id: props.pool.id
    }

    if (inputMode.value === 'iccid') {
      // ICCID模式
      const iccids = iccidText.value
        .split(/[\n,，]/)
        .map(s => s.trim())
        .filter(s => s.length > 0)
      
      // 去重
      requestData.iccids = Array.from(new Set(iccids))
    } else {
      // 选择卡片模式
      requestData.card_ids = selectedCards.value.map(c => c.id)
    }

    await addCardsToPool(requestData)
    ElMessage.success('添加成功')
    emit('success')
    handleClose()
  } catch (error: any) {
    if (error !== false) {
      console.error('添加失败:', error)
      ElMessage.error(error.message || '添加失败')
    }
  } finally {
    submitting.value = false
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  formRef.value?.resetFields()
  iccidText.value = ''
  selectedCards.value = []
  inputMode.value = 'iccid'
  visible.value = false
}

// 监听对话框打开
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      iccidText.value = ''
      selectedCards.value = []
      inputMode.value = 'iccid'
    }
  }
)
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.selected-cards {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>



