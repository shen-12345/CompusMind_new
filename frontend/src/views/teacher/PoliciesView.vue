<template>
  <div class="policies-page">
    <div class="page-header">
      <h2>{{ isTeacher ? '我的政策' : '全校政策管理' }}</h2>
      <p class="page-desc">{{ isTeacher ? '查看和管理您上传的所有政策' : '查看全校所有政策' }}</p>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" size="default">
        <el-form-item label="状态">
          <el-select v-model="filterStatus" placeholder="全部" clearable style="width: 130px" @change="fetchPolicies">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目分类" v-if="!isTeacher">
          <el-input v-model="filterCategory" placeholder="分类名称" clearable style="width: 150px" @keyup.enter="fetchPolicies" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchPolicies">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 政策列表 -->
    <el-card class="table-card">
      <el-table :data="policies" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="title" label="文件名" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetail(row.policy_id)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="学院" width="120" />
        <el-table-column prop="education_level" label="学历" width="70" />
        <el-table-column prop="project_category" label="分类" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row.policy_id)">
              查看
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              link
              type="success"
              size="small"
              @click="handlePublish(row)"
            >
              发布
            </el-button>
            <el-button
              v-if="row.status === 'published'"
              link
              type="warning"
              size="small"
              @click="handleWithdraw(row)"
            >
              撤回
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="fetchPolicies"
          @size-change="fetchPolicies"
        />
      </div>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="showDetail" title="政策详情" size="600px">
      <template v-if="detailData">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="文件名">{{ detailData.policy.title }}</el-descriptions-item>
          <el-descriptions-item label="学院">{{ detailData.policy.department }}</el-descriptions-item>
          <el-descriptions-item label="学历">{{ detailData.policy.education_level }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ detailData.policy.applicable_grades?.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ detailData.policy.project_category }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detailData.policy.status === 'published' ? 'success' : 'info'" size="small">
              {{ detailData.policy.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ formatTime(detailData.policy.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 20px 0 12px;">提取的元数据</h4>
        <el-descriptions v-if="detailData.metadata" :column="1" border>
          <el-descriptions-item label="项目名称">{{ detailData.metadata.project_name }}</el-descriptions-item>
          <el-descriptions-item label="截止时间">{{ detailData.metadata.deadline }}</el-descriptions-item>
          <el-descriptions-item label="硬性门槛">{{ detailData.metadata.prerequisites?.join('；') || '-' }}</el-descriptions-item>
          <el-descriptions-item label="材料清单">{{ detailData.metadata.material_list?.join('、') || '-' }}</el-descriptions-item>
          <el-descriptions-item label="评选流程">{{ detailData.metadata.review_process || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系方式">{{ detailData.metadata.contact_info || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="暂无元数据" />
      </template>
      <el-skeleton v-else :rows="6" animated />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPolicyList, getPolicyDetail, publishPolicy as publishApi } from '../../api/policy'
import { withdrawPolicy, deletePolicy } from '../../api/policyAdmin'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const isTeacher = computed(() => authStore.user?.role === 'teacher')

const policies = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filterStatus = ref('')
const filterCategory = ref('')
const showDetail = ref(false)
const detailData = ref<any>(null)

function formatTime(t: string) {
  if (!t) return '-'
  return t.replace('T', ' ').substring(0, 16)
}

async function fetchPolicies() {
  loading.value = true
  try {
    const res = await getPolicyList({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      department: filterCategory.value || undefined,
    })
    if (res.code === 0) {
      policies.value = res.data.items
      total.value = res.data.total
    }
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function viewDetail(policyId: number) {
  showDetail.value = true
  detailData.value = null
  try {
    const res = await getPolicyDetail(policyId)
    if (res.code === 0) {
      detailData.value = res.data
    }
  } catch {
    ElMessage.error('加载详情失败')
  }
}

async function handlePublish(row: any) {
  try {
    await ElMessageBox.confirm(`确定发布 "${row.title}" 吗？`, '提示', { type: 'info' })
    const res = await publishApi(row.policy_id)
    if (res.code === 0) {
      ElMessage.success('发布成功')
      fetchPolicies()
    }
  } catch {
    // 取消
  }
}

async function handleWithdraw(row: any) {
  try {
    await ElMessageBox.confirm(`撤回后学生将不可见，确定撤回 "${row.title}" 吗？`, '提示', { type: 'warning' })
    const res = await withdrawPolicy(row.policy_id)
    if (res.code === 0) {
      ElMessage.success('已撤回')
      fetchPolicies()
    }
  } catch {
    // 取消
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除草稿 "${row.title}" 吗？删除后不可恢复。`, '提示', {
      type: 'warning',
      confirmButtonText: '确认删除',
    })
    const res = await deletePolicy(row.policy_id)
    if (res.code === 0) {
      ElMessage.success('已删除')
      fetchPolicies()
    }
  } catch {
    // 取消
  }
}

onMounted(() => {
  fetchPolicies()
})
</script>

<style scoped>
.policies-page {
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
</style>