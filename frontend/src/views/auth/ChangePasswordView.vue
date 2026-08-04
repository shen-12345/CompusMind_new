<template>
  <div class="change-password-container">
    <div class="change-card">
      <div class="header">
        <h2>首次登录，请修改密码</h2>
        <p class="tip">为保障账号安全，请设置新密码</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        size="large"
        @keyup.enter="handleSubmit"
      >
        <el-form-item label="当前密码" prop="oldPassword">
          <el-input
            v-model="form.oldPassword"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="form.newPassword"
            type="password"
            show-password
            placeholder="8位以上，含大小写字母+数字+特殊字符"
            @input="onPasswordInput"
          />
          <div class="password-strength">
            <div
              class="strength-bar"
              :class="strengthClass"
              :style="{ width: strengthWidth + '%' }"
            />
          </div>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="submit-btn" @click="handleSubmit">
            {{ loading ? '提交中...' : '确认修改' }}
          </el-button>
        </el-form-item>
      </el-form>
      <el-alert
        v-if="errorMsg"
        :title="errorMsg"
        type="error"
        show-icon
        :closable="true"
        @close="errorMsg = ''"
        class="error-alert"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { changePassword } from '../../api/auth'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMsg = ref('')

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const validateNewPassword = (_rule: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error('请输入新密码'))
    return
  }
  if (value.length < 8) {
    callback(new Error('密码长度不能少于8位'))
    return
  }
  if (!/(?=.*[a-z])/.test(value)) {
    callback(new Error('密码必须包含小写字母'))
    return
  }
  if (!/(?=.*[A-Z])/.test(value)) {
    callback(new Error('密码必须包含大写字母'))
    return
  }
  if (!/(?=.*\d)/.test(value)) {
    callback(new Error('密码必须包含数字'))
    return
  }
  if (!/(?=.*[!@#$%^&*])/.test(value)) {
    callback(new Error('密码必须包含特殊字符(!@#$%^&*)'))
    return
  }
  callback()
}

const validateConfirm = (_rule: any, value: string, callback: any) => {
  if (value !== form.newPassword) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  callback()
}

const rules: FormRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, validator: validateNewPassword, trigger: ['blur', 'change'] },
  ],
  confirmPassword: [
    { required: true, validator: validateConfirm, trigger: ['blur', 'change'] },
  ],
}

// 密码强度指示器
const strengthWidth = computed(() => {
  let score = 0
  if (form.newPassword.length >= 8) score += 25
  if (/(?=.*[a-z])/.test(form.newPassword)) score += 25
  if (/(?=.*[A-Z])/.test(form.newPassword)) score += 25
  if (/(?=.*\d)/.test(form.newPassword)) score += 12.5
  if (/(?=.*[!@#$%^&*])/.test(form.newPassword)) score += 12.5
  return score
})

const strengthClass = computed(() => {
  if (strengthWidth.value < 50) return 'weak'
  if (strengthWidth.value < 75) return 'medium'
  return 'strong'
})

function onPasswordInput() {
  // 实时触发校验，消除旧错误消息的延迟
  formRef.value?.validateField('newPassword')
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  errorMsg.value = ''

  try {
    const res = await changePassword(form.oldPassword, form.newPassword)
    if (res.code === 0) {
      authStore.markPasswordChanged()
      ElMessage.success('密码修改成功，请重新登录')
      authStore.logout()
      router.push('/login')
    } else {
      errorMsg.value = res.message
    }
  } catch (err: any) {
    errorMsg.value = err.response?.data?.message || '修改失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.change-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f7fb;
}

.change-card {
  width: 500px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}

.header {
  text-align: center;
  margin-bottom: 32px;
}

.header h2 {
  font-size: 22px;
  color: #1a1a2e;
  margin: 0;
}

.tip {
  color: #888;
  font-size: 14px;
  margin-top: 8px;
}

.password-strength {
  height: 4px;
  background: #e8e8e8;
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.strength-bar {
  height: 100%;
  transition: all 0.3s;
  border-radius: 2px;
}

.strength-bar.weak {
  background: #f56c6c;
  width: 33%;
}

.strength-bar.medium {
  background: #e6a23c;
  width: 66%;
}

.strength-bar.strong {
  background: #67c23a;
  width: 100%;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 8px;
}

.error-alert {
  margin-top: 16px;
}
</style>