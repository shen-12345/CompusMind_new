<template>
  <div class="apps-page">
    <div class="page-header">
      <h2>我的申请</h2>
      <p class="page-desc">查看您所有的申请进度</p>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="applications.length === 0" class="empty-state">
      <el-empty description="暂无申请记录，去信息看板选择政策开始申请吧" />
    </div>

    <div v-else class="app-list">
      <el-card v-for="app in applications" :key="app.application_id" class="app-card" :class="statusClass(app.status)">
        <div class="app-header">
          <div class="app-title">{{ app.policy_title }}</div>
          <el-tag :type="statusTag(app.status)" size="small">{{ statusLabel(app.status) }}</el-tag>
        </div>

        <!-- 进度条 -->
        <div class="progress-bar">
          <div class="progress-step" v-for="s in steps" :key="s.step"
               :class="{ active: statusStep(app.status) >= s.step, done: statusStep(app.status) > s.step }">
            <div class="step-dot">{{ statusStep(app.status) > s.step ? '✓' : s.icon }}</div>
            <div class="step-label">{{ s.label }}</div>
          </div>
        </div>

        <div class="app-meta">
          <span>申请时间：{{ formatTime(app.applied_at) }}</span>
          <span v-if="app.submitted_at">提交时间：{{ formatTime(app.submitted_at) }}</span>
          <span>材料：{{ app.materials_uploaded }}/{{ app.materials_total }}</span>
        </div>

        <div class="app-actions">
          <el-button size="small" type="primary" @click="openProgress(app.application_id)">查看进度</el-button>
          <el-button v-if="app.status === 'preparing'" size="small" @click="openUpload(app)">上传材料</el-button>
          <el-button v-if="canAbandon(app.status)" size="small" type="danger" plain @click="handleAbandon(app)">放弃</el-button>
        </div>
      </el-card>
    </div>

    <!-- 上传材料对话框（仅"准备中"状态可用） -->
    <el-dialog v-model="showUpload" title="上传材料" width="500px" :close-on-click-modal="false">
      <template v-if="currentApp">
        <div class="material-list">
          <div v-for="m in currentApp.materials" :key="m.material_name" class="material-item">
            <div class="material-info">
              <span class="material-name">{{ m.material_name }}</span>
              <el-tag v-if="m.upload_status === 'uploaded'" type="success" size="small">已上传</el-tag>
              <el-tag v-else type="info" size="small">未上传</el-tag>
            </div>
            <div class="material-actions">
              <el-upload
                v-if="m.upload_status !== 'uploaded'"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="(f) => handleUpload(currentApp!.application_id, m.material_name, f.raw)"
                accept=".pdf,.jpg,.jpeg,.png"
              >
                <el-button size="small" type="primary">选择文件</el-button>
              </el-upload>
              <template v-else>
                <span class="file-name">{{ m.file_name }}</span>
                <el-button size="small" link type="danger" @click="handleDelete(currentApp!.application_id, m.material_name)">删除</el-button>
              </template>
            </div>
          </div>
        </div>
        <div class="submit-area" v-if="allUploaded(currentApp.materials)">
          <el-button type="primary" @click="handleSubmit(currentApp.application_id)" :loading="submitting">提交电子版</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 进度查看对话框（只读，展示申请状态和时间线） -->
    <el-dialog v-model="showProgress" title="申请进度" width="500px">
      <template v-if="progressData">
        <div class="progress-status">
          <el-steps :active="statusStep(progressData.application.status)" align-center finish-status="success">
            <el-step title="准备材料" />
            <el-step title="待初审" />
            <el-step title="初审通过" />
            <el-step title="待终核" />
            <el-step title="校级审批" />
            <el-step title="已完成" />
          </el-steps>
        </div>

        <el-descriptions :column="1" border size="small" class="progress-info">
          <el-descriptions-item label="当前状态">
            <el-tag :type="statusTag(progressData.application.status)" size="small">
              {{ statusLabel(progressData.application.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="申请时间">{{ formatTime(progressData.application.applied_at) }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatTime(progressData.application.submitted_at) || '未提交' }}</el-descriptions-item>
          <el-descriptions-item label="材料状态">
            {{ progressData.materials?.filter((m:any) => m.upload_status === 'uploaded').length || 0 }}/{{ progressData.materials?.length || 0 }} 已上传
          </el-descriptions-item>
        </el-descriptions>

        <h4 class="section-title">材料清单</h4>
        <div class="material-list">
          <div v-for="m in progressData.materials" :key="m.material_name" class="material-item">
            <span class="material-name">{{ m.material_name }}</span>
            <el-tag v-if="m.upload_status === 'uploaded'" type="success" size="small">已上传</el-tag>
            <el-tag v-else type="info" size="small">未上传</el-tag>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getApplications, uploadMaterial, deleteMaterial, submitApplication, abandonApplication, getApplicationDetail } from '../../api/application'

const loading = ref(true)
const applications = ref<any[]>([])
const showUpload = ref(false)
const showProgress = ref(false)
const currentApp = ref<any>(null)
const progressData = ref<any>(null)
const submitting = ref(false)

const steps = [
  { step: 1, label: '准备材料', icon: '📝' },
  { step: 2, label: '待初审', icon: '⏳' },
  { step: 3, label: '初审通过', icon: '✅' },
  { step: 4, label: '待终核', icon: '⏳' },
  { step: 5, label: '校级审批', icon: '⏳' },
  { step: 6, label: '已完成', icon: '🎉' },
]

function statusStep(s: string) {
  const map: Record<string, number> = {
    preparing: 1, submitted: 2, pending_review: 2, needs_revision: 1,
    '初审通过': 3, pending_final: 4, '待终核': 4, pending_admin: 5,
    completed: 6, abandoned: 0,
  }
  return map[s] || 0
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    preparing: '准备中', submitted: '待初审', pending_review: '待初审',
    needs_revision: '需修正', '初审通过': '初审通过', pending_final: '待终核',
    '待终核': '待终核', pending_admin: '校级审批', completed: '已完成', abandoned: '已放弃',
  }
  return map[s] || s
}

function statusTag(s: string) {
  const map: Record<string, string> = {
    preparing: 'warning', submitted: 'primary', completed: 'success',
    abandoned: 'info', needs_revision: 'danger', '初审通过': 'success',
  }
  return map[s] || 'info'
}

function statusClass(s: string) {
  return s === 'abandoned' ? 'abandoned' : s === 'completed' ? 'completed' : ''
}

function canAbandon(s: string) {
  return ['preparing', 'submitted', 'needs_revision'].includes(s)
}

function formatTime(t: string) {
  if (!t) return '-'
  return t.replace('T', ' ').substring(0, 16)
}

function allUploaded(materials: any[]) {
  return materials?.every((m: any) => m.upload_status === 'uploaded')
}

async function fetchApps() {
  loading.value = true
  try {
    const res = await getApplications()
    if (res.code === 0) applications.value = res.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

async function openUpload(appId: number) {
  try {
    const res = await getApplicationDetail(appId)
    if (res.code === 0) {
      currentApp.value = res.data
      showUpload.value = true
    }
  } catch { ElMessage.error('加载失败') }
}

async function openProgress(appId: number) {
  try {
    const res = await getApplicationDetail(appId)
    if (res.code === 0) {
      progressData.value = res.data
      showProgress.value = true
    }
  } catch { ElMessage.error('加载失败') }
}

async function handleUpload(appId: number, name: string, file: File) {
  try {
    const res = await uploadMaterial(appId, name, file)
    if (res.code === 0) {
      ElMessage.success('上传成功')
      await openUpload(appId)
    }
  } catch { ElMessage.error('上传失败') }
}

async function handleDelete(appId: number, name: string) {
  try {
    const res = await deleteMaterial(appId, name)
    if (res.code === 0) {
      ElMessage.success('已删除')
      await openUpload(appId)
    }
  } catch { ElMessage.error('删除失败') }
}

async function handleSubmit(appId: number) {
  submitting.value = true
  try {
    const res = await submitApplication(appId)
    if (res.code === 0) {
      ElMessage.success('提交成功')
      showUpload.value = false
      await fetchApps()
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '提交失败')
  } finally { submitting.value = false }
}

async function handleAbandon(app: any) {
  try {
    await ElMessageBox.confirm('确定放弃该申请吗？', '提示', { type: 'warning' })
    const res = await abandonApplication(app.application_id)
    if (res.code === 0) {
      ElMessage.success('已放弃')
      await fetchApps()
    }
  } catch {}
}

onMounted(fetchApps)
</script>

<style scoped>
.apps-page { padding: 24px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; color: #1a1a2e; margin: 0; }
.page-desc { color: #888; font-size: 14px; margin-top: 4px; }
.app-card { margin-bottom: 16px; }
.app-card.abandoned { opacity: 0.6; }
.app-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.app-title { font-size: 16px; font-weight: 600; color: #1a1a2e; }
.progress-bar { display: flex; justify-content: space-between; margin-bottom: 12px; padding: 0 8px; }
.progress-step { text-align: center; flex: 1; position: relative; }
.progress-step:not(:last-child)::after {
  content: ''; position: absolute; top: 12px; left: 50%; width: 100%;
  height: 2px; background: #e8e8e8; z-index: 0;
}
.progress-step.active:not(:last-child)::after { background: #409eff; }
.step-dot {
  width: 24px; height: 24px; border-radius: 50%; background: #e8e8e8;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px; position: relative; z-index: 1;
}
.progress-step.active .step-dot { background: #409eff; color: #fff; }
.progress-step.done .step-dot { background: #67c23a; color: #fff; }
.step-label { font-size: 11px; color: #999; margin-top: 4px; }
.progress-step.active .step-label { color: #409eff; font-weight: 600; }
.app-meta { display: flex; gap: 20px; font-size: 13px; color: #888; margin-bottom: 12px; }
.app-actions { display: flex; gap: 8px; }
.material-list { padding: 8px 0; }
.material-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f0f0f0; }
.material-info { display: flex; gap: 8px; align-items: center; }
.material-name { font-size: 14px; }
.file-name { font-size: 13px; color: #606266; }
.material-actions { display: flex; gap: 8px; align-items: center; }
.submit-area { margin-top: 20px; text-align: center; }
.loading-state { padding: 40px; }
.progress-status { margin-bottom: 24px; padding: 16px 0; }
.progress-info { margin-bottom: 16px; }
.section-title { font-size: 15px; margin: 16px 0 8px; color: #1a1a2e; }
</style>