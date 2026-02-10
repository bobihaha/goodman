<template>
  <el-dialog
    v-model="visible"
    title="批量划拨"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="选中卡片">
        <el-tag type="info">{{ cardIds.length }} 张卡片</el-tag>
      </el-form-item>

      <el-form-item label="目标用户" prop="to_user_id">
        <el-select
          v-model="form.to_user_id"
          placeholder="请选择目标用户"
          filterable
          remote
          :remote-method="searchUsers"
          :loading="userLoading"
          style="width: 100%"
        >
          <el-option
            v-for="user in userList"
            :key="user.id"
            :label="`${user.account} (${user.name})`"
            :value="user.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="备注" prop="remark">
        <el-input
          v-model="form.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入划拨备注（可选）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确定划拨
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { cardApi } from '@/api'
import { userApi } from '@/api'
import type { User } from '@/types/user'

interface Props {
  modelValue: boolean
  cardIds: number[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 数据
const formRef = ref<FormInstance>()
const loading = ref(false)
const userLoading = ref(false)
const userList = ref<User[]>([])

const form = ref({
  to_user_id: undefined as number | undefined,
  remark: ''
})

// 表单验证规则
const rules: FormRules = {
  to_user_id: [
    { required: true, message: '请选择目标用户', trigger: 'change' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 搜索用户
const searchUsers = async (query: string) => {
  if (!query) {
    userList.value = []
    return
  }

  userLoading.value = true
  try {
    const response = await userApi.getList({
      keyword: query,
      page: 1,
      page_size: 20
    })
    userList.value = response.list
  } catch (error) {
    console.error('搜索用户失败:', error)
  } finally {
    userLoading.value = false
  }
}

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const result = await cardApi.batchTransfer({
        card_ids: props.cardIds,
        to_user_id: form.value.to_user_id!,
        remark: form.value.remark || undefined
      })

      ElMessage.success(`成功划拨 ${result.success} 张卡片`)
      emit('success')
      handleClose()
    } catch (error) {
      console.error('批量划拨失败:', error)
    } finally {
      loading.value = false
    }
  })
}

// 关闭
const handleClose = () => {
  visible.value = false
}

// 重置表单
const resetForm = () => {
  form.value = {
    to_user_id: undefined,
    remark: ''
  }
  formRef.value?.clearValidate()
}

// 监听对话框关闭
watch(visible, (newVal) => {
  if (!newVal) {
    setTimeout(resetForm, 300)
  }
})
</script>


