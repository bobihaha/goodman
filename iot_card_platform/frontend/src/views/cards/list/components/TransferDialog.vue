<template>
  <el-dialog
    v-model="visible"
    title="单卡划拨"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="ICCID">
        <el-input :value="card?.iccid" disabled />
      </el-form-item>

      <el-form-item label="目标用户" prop="target_user_id">
        <el-select
          v-model="form.target_user_id"
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
import type { Card } from '@/types/card'
import type { User } from '@/types/user'

interface Props {
  modelValue: boolean
  card: Card | null
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
  target_user_id: undefined as number | undefined,
  remark: ''
})

// 表单验证规则
const rules: FormRules = {
  target_user_id: [
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
  if (!formRef.value || !props.card) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await cardApi.transfer(
        props.card!.id,
        form.value.target_user_id!,
        form.value.remark || undefined
      )

      ElMessage.success('划拨成功')
      emit('success')
      handleClose()
    } catch (error) {
      console.error('划拨失败:', error)
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
    target_user_id: undefined,
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





