<template>
  <div class="channel-login"><div class="login-card"><h1>渠道积分中心</h1><p>查看客户订单与推广积分</p><el-form ref="formRef" :model="form" :rules="rules" size="large"><el-form-item prop="account"><el-input v-model="form.account" placeholder="渠道账号" /></el-form-item><el-form-item prop="password"><el-input v-model="form.password" type="password" show-password placeholder="登录密码" @keyup.enter="login" /></el-form-item><el-button type="primary" class="login-button" :loading="loading" @click="login">登录</el-button></el-form></div></div>
</template>
<script setup lang="ts">
import { reactive, ref } from 'vue'; import { useRouter } from 'vue-router'; import { ElMessage, type FormInstance, type FormRules } from 'element-plus'; import { channelPortalApi } from '@/api/modules/channel'
const router=useRouter(); const formRef=ref<FormInstance>(); const loading=ref(false); const form=reactive({account:'',password:''}); const rules:FormRules={account:[{required:true,message:'请输入账号'}],password:[{required:true,min:8,message:'请输入密码'}]}
const login=async()=>{await formRef.value?.validate();loading.value=true;try{const data=await channelPortalApi.login(form);localStorage.setItem('channel_access_token',data.access_token);localStorage.setItem('channel_partner',JSON.stringify(data.partner));await router.push('/channel/points')}catch(error:any){ElMessage.error(error.message||'登录失败')}finally{loading.value=false}}
</script>
<style scoped>.channel-login{min-height:100vh;display:grid;place-items:center;background:#f3f6fb}.login-card{width:400px;max-width:calc(100vw - 40px);padding:40px;background:#fff;border-radius:16px;box-shadow:0 16px 45px rgba(31,68,119,.12)}h1{margin:0 0 8px}p{color:#909399;margin:0 0 28px}.login-button{width:100%}</style>
