<template>
  <div class="audit-page">
    <div class="page-header">
      <h2>审计日志</h2>
      <p class="page-desc">查看系统的所有操作记录。</p>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" size="default">
        <el-form-item label="操作类型">
          <el-select v-model="filters.action" placeholder="全部" clearable style="width: 150px" @change="fetchLogs">
            <el-option label="登录" value="user_login" />
            <el-option label="创建用户" value="user_create" />
            <el-option label="编辑用户" value="user_update" />
            <el-option label="启用/禁用" value="user_toggle_active" />
            <el-option label="批量导入" value="user_batch_import" />
            <el-option label="修改密码" value="change_password" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="filters.operator_name" placeholder="操作人姓名" clearable style="width: 150px" @keyup.enter="fetchLogs" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchLogs">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志表格 -->
    <el-card class="table-card">
      <el-table :data="logs" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="created_at" label="操作时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="100" />
        <el-table-column prop="action" label="操作类型" width="120">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action)" size="small">
              {{ actionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource_type" label="资源类型" width="100" />
        <el-table-column prop="resource_id" label="资源 ID" width="80" />
        <el-table-column prop="ip_address" label="IP 地址" width="130" />
        <el-table-column label="操作详情" min-width="200">
          <template #default="{ row }">
            <el-button
              v-if="row.detail && row.detail !== 'null'"
              link
              type="primary"
              size="small"
              @click="showDetail(row.detail)"
            >
              查看详情
            </el-button>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="fetchLogs"
          @size-change="fetchLogs"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="操作详情" width="500px">
      <pre class="detail-json">{{ detailContent }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAuditLogs } from '../../api/admin/auditLogs'

interface LogItem {
  log_id: number
  operator_name: string
  action: string
  resource_type: string
  resource_id: number | null
  detail: any
  ip_address: string | null
  created_at: string | null
}

const logs = ref<LogItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const showDetailDialog = ref(false)
const detailContent = ref('')

const filters = reactive({
  action: '',
  operator_name: '',
})

function actionLabel(action: string) {
  const map: Record<string, string> = {
    user_login: '登录',
    user_create: '创建用户',
    user_update: '编辑用户',
    user_toggle_active: '启用/禁用',
    user_batch_import: '批量导入',
    change_password: '修改密码',
  }
  return map[action] || action
}

function actionTagType(action: string) {
  const map: Record<string, string> = {
    user_login: 'info',
    user_create: 'success',
    user_update: 'warning',
    user_toggle_active: 'danger',
    user_batch_import: 'primary',
    change_password: '',
  }
  return map[action] || 'info'
}

function formatTime(t: string) {
  if (!t) return '-'
  return t.replace('T', ' ').substring(0, 19)
}

async function fetchLogs() {
  loading.value = true
  try {
    const res = await getAuditLogs({
      page: page.value,
      page_size: pageSize.value,
      action: filters.action || undefined,
      operator_name: filters.operator_name || undefined,
    })
    if (res.code === 0) {
      logs.value = res.data.items
      total.value = res.data.total
    }
  } catch {
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.action = ''
  filters.operator_name = ''
  page.value = 1
  fetchLogs()
}

function showDetail(detail: any) {
  if (typeof detail === 'object') {
    detailContent.value = JSON.stringify(detail, null, 2)
  } else {
    detailContent.value = String(detail)
  }
  showDetailDialog.value = true
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.audit-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 16px;
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

.filter-card {
  margin-bottom: 16px;
}

.table-card {
  min-height: 300px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.detail-json {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>