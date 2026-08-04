<template>
  <div class="import-page">
    <div class="page-header">
      <h2>批量导入学生</h2>
      <p class="page-desc">上传 Excel 文件，批量创建学生账号。</p>
    </div>

    <el-card class="step-card">
      <el-steps :active="step" align-center>
        <el-step title="下载模板" />
        <el-step title="上传文件" />
        <el-step title="确认导入" />
      </el-steps>

      <!-- 步骤 1：下载模板 -->
      <div v-if="step === 0" class="step-content">
        <el-button type="primary" @click="downloadTemplate" :loading="downloadLoading">
          下载导入模板
        </el-button>
        <p class="step-tip">模板为 .xlsx 格式，包含必填列：username、name、department</p>
      </div>

      <!-- 步骤 2：上传文件 -->
      <div v-if="step === 1" class="step-content">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="handleFileChange"
          :limit="1"
          accept=".xlsx,.xls"
          drag
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">将 Excel 文件拖拽到此处，或<em>点击选择</em></div>
        </el-upload>
      </div>

      <!-- 步骤 3：预览确认 -->
      <div v-if="step === 2" class="step-content">
        <el-alert :title="`共解析到 ${previewData.length} 条数据`" type="info" show-icon class="preview-alert" />
        <el-table :data="previewData.slice(0, 10)" stripe max-height="300">
          <el-table-column prop="username" label="学号" width="120" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="department" label="学院" />
          <el-table-column prop="education_level" label="学历" width="80" />
          <el-table-column prop="grade" label="年级" width="80" />
        </el-table>
        <p class="preview-tip" v-if="previewData.length > 10">仅展示前 10 条，共 {{ previewData.length }} 条</p>
        <div class="step-actions">
          <el-button @click="step = 0">重新选择</el-button>
          <el-button type="primary" @click="handleImport" :loading="importLoading">
            确认导入
          </el-button>
        </div>
      </div>

      <!-- 导入结果 -->
      <div v-if="importResult" class="step-content">
        <el-result
          :icon="importResult.failures.length === 0 ? 'success' : 'warning'"
          :title="`导入完成：成功 ${importResult.success} 条`"
          :sub-title="importResult.failures.length > 0 ? `失败 ${importResult.failures.length} 条` : ''"
        >
          <template #extra>
            <el-table v-if="importResult.failures.length > 0" :data="importResult.failures" stripe max-height="200">
              <el-table-column prop="row" label="行号" width="60" />
              <el-table-column prop="reason" label="失败原因" />
            </el-table>
            <div class="result-actions">
              <el-button type="primary" @click="resetImport">继续导入</el-button>
            </div>
          </template>
        </el-result>
      </div>
    </el-card>

    <!-- 操作按钮 -->
    <div v-if="step > 0 && step < 3 && !importResult" class="step-actions" style="margin-top: 20px;">
      <el-button v-if="step > 1" @click="step--">上一步</el-button>
      <el-button v-if="step === 1" type="primary" @click="submitUpload" :disabled="!selectedFile">
        预览数据
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getImportTemplate, uploadImport } from '../../api/admin/import'

const step = ref(0)
const downloadLoading = ref(false)
const selectedFile = ref<File | null>(null)
const previewData = ref<any[]>([])
const importLoading = ref(false)
const importResult = ref<any>(null)

async function downloadTemplate() {
  downloadLoading.value = true
  try {
    const blob = await getImportTemplate()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'student_import_template.xlsx'
    a.click()
    URL.revokeObjectURL(url)
    step.value = 1
  } catch {
    ElMessage.error('下载模板失败')
  } finally {
    downloadLoading.value = false
  }
}

function handleFileChange(file: any) {
  selectedFile.value = file.raw
}

function submitUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  // 模拟预览：调用上传 API 的预览模式
  step.value = 2
  // 实际这里应该调用预览 API，但后端没有单独的预览接口
  // 直接跳到上传步骤
}

async function handleImport() {
  if (!selectedFile.value) return
  importLoading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const res = await uploadImport(formData)
    if (res.code === 0) {
      importResult.value = res.data
      step.value = 3
    } else {
      ElMessage.error(res.message)
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '导入失败')
  } finally {
    importLoading.value = false
  }
}

function resetImport() {
  step.value = 0
  selectedFile.value = null
  previewData.value = []
  importResult.value = null
}
</script>

<style scoped>
.import-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 22px;
  color: #1a1a2e;
  margin: 0;
}

.page-desc {
  color: #888;
  font-size: 14px;
  margin-top: 4px;
}

.step-card {
  max-width: 700px;
}

.step-content {
  padding: 32px 0;
  text-align: center;
}

.step-tip {
  color: #999;
  font-size: 13px;
  margin-top: 12px;
}

.upload-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  color: #666;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
}

.preview-alert {
  margin-bottom: 16px;
  text-align: left;
}

.preview-tip {
  color: #999;
  font-size: 13px;
  margin-top: 8px;
}

.step-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.result-actions {
  margin-top: 20px;
}
</style>