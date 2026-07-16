<template>
  <div class="register-page">
    <div class="register-card">
      <div class="brand">{{ config?.channel_name || '客户信息登记' }}</div>
      <h1>客户信息登记</h1>
      <p class="intro">提交后平台将创建客户档案，并锁定本渠道服务关系。</p>
      <el-result v-if="pageError" icon="error" title="页面不可用" :sub-title="pageError" />
      <el-result v-else-if="success" icon="success" title="登记成功" sub-title="客户档案已创建，请勿重复提交。" />
      <el-form v-else ref="formRef" :model="form" :rules="rules" label-position="top" size="large" @submit.prevent="submit">
        <el-form-item label="客户姓名" prop="customer_name"><el-input v-model="form.customer_name" maxlength="50" placeholder="请输入客户姓名" /></el-form-item>
        <el-form-item label="手机号" prop="customer_phone"><el-input v-model="form.customer_phone" maxlength="11" inputmode="numeric" placeholder="请输入手机号" /></el-form-item>
        <el-form-item label="用户情况（设备、场景、规模）" prop="customer_profile">
          <el-input v-model="form.customer_profile" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="例如：4G工业网关，用于工厂设备数据采集，预计首批80台" />
        </el-form-item>
        <el-form-item prop="consent"><el-checkbox v-model="form.consent">我已阅读并同意提交信息用于客户建档和渠道服务归属</el-checkbox></el-form-item>
        <el-button native-type="submit" type="primary" class="submit" :loading="submitting">确认提交</el-button>
        <div class="privacy">本页面不发送短信验证码。请确认姓名、手机号真实准确，渠道归属提交后不可自行修改。</div>
        <router-link class="partner-login" to="/channel/login">渠道伙伴登录 · 查看推荐客户与积分</router-link>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { channelPortalApi } from '@/api/modules/channel'
const route = useRoute(); const slug = String(route.params.slug || '')
const config = ref<{ channel_name: string } | null>(null); const formRef = ref<FormInstance>(); const submitting = ref(false); const success = ref(false); const pageError = ref('')
const form = reactive({ customer_name: '', customer_phone: '', customer_profile: '', consent: false })
const rules: FormRules = {
  customer_name: [{ required: true, min: 2, message: '请输入至少2个字符的客户姓名' }],
  customer_phone: [{ required: true, pattern: /^1[3-9]\d{9}$/, message: '请输入正确手机号' }],
  customer_profile: [{ required: true, min: 5, message: '请填写设备、使用场景和预计规模' }],
  consent: [{ validator: (_r, value, callback) => value ? callback() : callback(new Error('请先同意隐私告知')) }]
}
const submit = async () => {
  if (submitting.value || !formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请完整填写必填信息')
    return
  }
  submitting.value = true
  try {
    await channelPortalApi.register(slug, form)
    success.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '提交失败')
  } finally {
    submitting.value = false
  }
}
onMounted(async () => { try { config.value = await channelPortalApi.getPublicConfig(slug) } catch (error: any) { pageError.value = error.message || '该渠道报备页面不存在或已停用' } })
</script>

<style scoped>
.register-page{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;background:linear-gradient(145deg,#eef5ff,#f7f9fc)}.register-card{width:min(100%,500px);padding:32px;background:#fff;border-radius:18px;box-shadow:0 18px 50px rgba(35,83,145,.12)}.brand{color:#1677ff;font-weight:700}.register-card h1{margin:12px 0 8px;font-size:28px}.intro,.privacy{color:#7a8493;line-height:1.7}.submit{width:100%;margin-top:8px}.privacy{font-size:12px;margin-top:18px}.partner-login{display:block;margin-top:18px;text-align:center;color:#1677ff;text-decoration:none;font-size:14px}.register-card :deep(.el-checkbox){height:auto;align-items:flex-start;white-space:normal}.register-card :deep(.el-checkbox__input){margin-top:3px}.register-card :deep(.el-checkbox__label){white-space:normal;line-height:1.5}
</style>
