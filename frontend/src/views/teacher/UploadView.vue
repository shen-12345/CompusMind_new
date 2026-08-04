<template>
  <div class="upload-page">
    <div class="page-header">
      <h2>{{ isPreview ? '解析预览' : '上传政策' }}</h2>
      <p class="page-desc">{{ isPreview ? '核对系统提取的信息，确认无误后发布' : '上传政策通知文档，系统自动提取关键信息' }}</p>
    </div>

    <!-- 上传表单 -->
    <el-card v-if="!isPreview" class="form-card">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="政策文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".pdf,.docx"
            drag
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">
              将 PDF 或 Word 文件拖拽到此处，或<em>点击选择</em>
            </div>
            <template #tip>
              <div class="upload-tip">支持 PDF、.docx 格式，最大 20MB</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="发布学院" prop="department">
          <el-input v-model="form.department" :disabled="isTeacher" placeholder="如：计算机学院" />
          <div v-if="isTeacher" class="form-tip">自动使用您所在的学院</div>
        </el-form-item>

        <el-form-item label="适用学历" prop="education_level">
          <el-select v-model="form.education_level" style="width: 100%">
            <el-option label="本科" value="本科" />
            <el-option label="硕士" value="硕士" />
            <el-option label="博士" value="博士" />
            <el-option label="全校" value="全校" />
          </el-select>
        </el-form-item>

        <el-form-item label="适用年级" prop="applicable_grades">
          <el-select v-model="form.applicable_grades" multiple style="width: 100%" placeholder="选择年级">
            <el-option label="2021 级" value="2021" />
            <el-option label="2022 级" value="2022" />
            <el-option label="2023 级" value="2023" />
            <el-option label="2024 级" value="2024" />
            <el-option label="2025 级" value="2025" />
            <el-option label="2026 级" value="2026" />
          </el-select>
        </el-form-item>

        <el-form-item label="项目分类" prop="project_category">
          <el-input v-model="form.project_category" placeholder="如：奖学金、助学金、报销" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="uploadLoading" @click="handleUpload" size="large">
            {{ uploadLoading ? '上传中...' : '开始上传' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 上传进度 -->
    <el-card v-if="uploadLoading" class="progress-card">
      <el-progress :percentage="uploadProgress" :stroke-width="8" />
      <p class="progress-text">{{ uploadStatusText }}</p>
    </el-card>

    <!-- 解析预览 -->
    <template v-if="isPreview">
      <el-card class="preview-card">
        <template #header>
          <div class="preview-header">
            <span>📋 提取的字段信息</span>
            <el-tag type="warning" v-if="metadata">置信度: {{ metadata.confidence_score || 'N/A' }}</el-tag>
          </div>
        </template>

        <el-form :model="editForm" label-width="120px">
          <el-form-item label="项目名称">
            <el-input v-model="editForm.project_name" />
          </el-form-item>
          <el-form-item label="截止时间">
            <el-date-picker
              v-model="editForm.deadline"
              type="datetime"
              placeholder="选择截止时间"
              format="YYYY-MM-DD HH:mm"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="硬性门槛">
            <el-tag
              v-for="(item, i) in editForm.prerequisites"
              :key="i"
              closable
              :disable-transitions="true"
              style="margin: 0 4px 4px 0"
              @close="editForm.prerequisites.splice(i, 1)"
            >
              {{ item }}
            </el-tag>
            <el-input
              v-if="showPrereqInput"
              v-model="prereqInput"
              size="small"
              style="width: 200px"
              @keyup.enter="addPrereq"
              @blur="addPrereq"
            />
            <el-button v-else size="small" link @click="showPrereqInput = true">+ 添加</el-button>
          </el-form-item>
          <el-form-item label="互斥项">
            <el-tag
              v-for="(item, i) in editForm.mutually_exclusive"
              :key="i"
              closable
              :disable-transitions="true"
              style="margin: 0 4px 4px 0"
              @close="editForm.mutually_exclusive.splice(i, 1)"
            >
              {{ item }}
            </el-tag>
            <el-input
              v-if="showMutualInput"
              v-model="mutualInput"
              size="small"
              style="width: 200px"
              @keyup.enter="addMutual"
              @blur="addMutual"
            />
            <el-button v-else size="small" link @click="showMutualInput = true">+ 添加</el-button>
          </el-form-item>
          <el-form-item label="材料清单">
            <el-tag
              v-for="(item, i) in editForm.material_list"
              :key="i"
              closable
              :disable-transitions="true"
              style="margin: 0 4px 4px 0"
              @close="editForm.material_list.splice(i, 1)"
            >
              {{ item }}
            </el-tag>
            <el-input
              v-if="showMaterialInput"
              v-model="materialInput"
              size="small"
              style="width: 200px"
              @keyup.enter="addMaterial"
              @blur="addMaterial"
            />
            <el-button v-else size="small" link @click="showMaterialInput = true">+ 添加</el-button>
          </el-form-item>
          <el-form-item label="评选流程">
            <el-input v-model="editForm.review_process" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="联系方式">
            <el-input v-model="editForm.contact_info" />
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 原文预览 -->
      <el-card class="preview-card">
        <template #header>
          <span>📄 文档原文</span>
        </template>
        <pre class="doc-preview">{{ policyContent }}</pre>
      </el-card>

      <!-- 操作按钮 -->
      <div class="preview-actions">
        <el-button size="large" @click="isPreview = false">返回修改</el-button>
        <el-button type="success" size="large" :loading="publishLoading" @click="handleSaveDraft">
          保存草稿
        </el-button>
        <el-button type="primary" size="large" :loading="publishLoading" @click="handlePublish">
          确认发布
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadPolicy, extractMetadata, getPolicyDetail, publishPolicy } from '../../api/policy'
import { useAuthStore } from '../../stores/auth'
import type { FormInstance, FormRules } from 'element-plus'

const authStore = useAuthStore()
const isTeacher = computed(() => authStore.user?.role === 'teacher')

const formRef = ref<FormInstance>()
const uploadRef = ref()
const uploadLoading = ref(false)
const uploadProgress = ref(0)
const uploadStatusText = ref('')
const selectedFile = ref<File | null>(null)
const isPreview = ref(false)
const policyId = ref<number | null>(null)
const policyContent = ref('')
const publishLoading = ref(false)

const form = reactive({
  department: '',
  education_level: '本科',
  applicable_grades: [] as string[],
  project_category: '',
})

const rules: FormRules = {
  department: [{ required: true, message: '请输入发布学院', trigger: 'blur' }],
  education_level: [{ required: true, message: '请选择适用学历', trigger: 'change' }],
  applicable_grades: [{ required: true, message: '请选择适用年级', trigger: 'change' }],
  project_category: [{ required: true, message: '请输入项目分类', trigger: 'blur' }],
}

// 编辑表单
const metadata = ref<any>(null)
const editForm = reactive({
  project_name: '',
  deadline: null as any,
  prerequisites: [] as string[],
  mutually_exclusive: [] as string[],
  material_list: [] as string[],
  review_process: '',
  contact_info: '',
})

const showPrereqInput = ref(false)
const prereqInput = ref('')
const showMutualInput = ref(false)
const mutualInput = ref('')
const showMaterialInput = ref(false)
const materialInput = ref('')

function addPrereq() {
  if (prereqInput.value.trim()) {
    editForm.prerequisites.push(prereqInput.value.trim())
    prereqInput.value = ''
  }
  showPrereqInput.value = false
}

function addMutual() {
  if (mutualInput.value.trim()) {
    editForm.mutually_exclusive.push(mutualInput.value.trim())
    mutualInput.value = ''
  }
  showMutualInput.value = false
}

function addMaterial() {
  if (materialInput.value.trim()) {
    editForm.material_list.push(materialInput.value.trim())
    materialInput.value = ''
  }
  showMaterialInput.value = false
}

function handleFileChange(file: any) {
  selectedFile.value = file.raw
}

async function handleUpload() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }

  uploadLoading.value = true
  uploadProgress.value = 10
  uploadStatusText.value = '正在上传...'

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('department', form.department)
    formData.append('education_level', form.education_level)
    formData.append('applicable_grades', JSON.stringify(form.applicable_grades))
    formData.append('project_category', form.project_category)

    const res = await uploadPolicy(formData)
    if (res.code === 0) {
      uploadProgress.value = 50
      uploadStatusText.value = '上传成功，正在提取信息...'
      policyId.value = res.data.policy_id

      // 调用 LLM 提取
      const extractRes = await extractMetadata(res.data.policy_id)
      if (extractRes.code === 0) {
        metadata.value = extractRes.data
        // 填充编辑表单
        editForm.project_name = extractRes.data.project_name || ''
        editForm.deadline = extractRes.data.deadline || null
        editForm.prerequisites = extractRes.data.prerequisites || []
        editForm.mutually_exclusive = extractRes.data.mutually_exclusive || []
        editForm.material_list = extractRes.data.material_list || []
        editForm.review_process = extractRes.data.review_process || ''
        editForm.contact_info = extractRes.data.contact_info || ''
      }

      // 获取政策详情（含原文）
      const detailRes = await getPolicyDetail(res.data.policy_id)
      if (detailRes.code === 0) {
        policyContent.value = detailRes.data.policy.title + '\n\n（原文内容已提取）'
      }

      uploadProgress.value = 100
      uploadStatusText.value = '解析完成'
      isPreview.value = true
    } else {
      ElMessage.error(res.message)
      uploadLoading.value = false
      return
    }

    // 调用 LLM 提取（独立 try/catch，提取失败不影响上传）
    uploadProgress.value = 50
    uploadStatusText.value = '正在提取信息...'
    try {
      const extractRes = await extractMetadata(res.data.policy_id)
      if (extractRes.code === 0) {
        metadata.value = extractRes.data
        editForm.project_name = extractRes.data.project_name || ''
        editForm.deadline = extractRes.data.deadline || null
        editForm.prerequisites = extractRes.data.prerequisites || []
        editForm.mutually_exclusive = extractRes.data.mutually_exclusive || []
        editForm.material_list = extractRes.data.material_list || []
        editForm.review_process = extractRes.data.review_process || ''
        editForm.contact_info = extractRes.data.contact_info || ''
      }
    } catch {
      // 提取失败不影响，用户可手动填写
    }

    // 获取政策详情
    try {
      const detailRes = await getPolicyDetail(res.data.policy_id)
      if (detailRes.code === 0) {
        policyContent.value = detailRes.data.policy.title + '\n\n（原文内容已提取）'
      }
    } catch {
      // 获取详情失败不影响
    }

    uploadProgress.value = 100
    uploadStatusText.value = '解析完成'
    isPreview.value = true
    uploadLoading.value = false
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '上传失败')
    uploadLoading.value = false
  }
}

async function handlePublish() {
  if (!policyId.value) return
  publishLoading.value = true
  try {
    const res = await publishPolicy(policyId.value, {
      project_name: editForm.project_name,
      deadline: editForm.deadline,
      prerequisites: editForm.prerequisites,
      mutually_exclusive: editForm.mutually_exclusive,
      material_list: editForm.material_list,
      review_process: editForm.review_process,
      contact_info: editForm.contact_info,
    })
    if (res.code === 0) {
      ElMessage.success('发布成功')
      isPreview.value = false
      // 重置表单
      form.department = ''
      form.applicable_grades = []
      form.project_category = ''
      selectedFile.value = null
    } else {
      ElMessage.error(res.message)
    }
  } catch (err: any) {
    ElMessage.error('发布失败')
  } finally {
    publishLoading.value = false
  }
}

async function handleSaveDraft() {
  ElMessage.success('已保存草稿')
  isPreview.value = false
}

// 自动填充辅导员所属学院
onMounted(() => {
  if (isTeacher.value && authStore.user?.department) {
    form.department = authStore.user.department
  }
})
</script>

<style scoped>
.upload-page {
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

.form-card {
  max-width: 700px;
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

.upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.progress-card {
  max-width: 700px;
  margin-top: 16px;
  padding: 24px;
}

.progress-text {
  text-align: center;
  margin-top: 12px;
  color: #666;
  font-size: 14px;
}

.preview-card {
  margin-top: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.doc-preview {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}

.preview-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
  padding-bottom: 24px;
}
</style>