<template>
  <div class="dashboard-page">
    <!-- 欢迎条 -->
    <div class="welcome-banner">
      <h2>信息看板</h2>
      <p class="welcome-text">{{ userName }}同学，您有 {{ total }} 个可申请的政策</p>
    </div>

    <!-- 政策卡片列表 -->
    <div v-if="policies.length > 0" class="policy-list">
      <div
        v-for="item in policies"
        :key="item.policy_id"
        class="policy-card"
        :class="{ 'urgent': isUrgent(item) }"
        @click="openDetail(item)"
      >
        <div class="card-header">
          <h3 class="card-title">{{ item.title }}</h3>
          <el-tag :type="item.status === 'published' ? 'success' : 'info'" size="small">
            {{ item.status === 'published' ? '可申请' : '已截止' }}
          </el-tag>
        </div>
        <div class="card-body">
          <div class="card-info">
            <span class="info-label">发布学院</span>
            <span class="info-value">{{ item.department }}</span>
          </div>
          <div class="card-info">
            <span class="info-label">项目分类</span>
            <span class="info-value">{{ item.project_category }}</span>
          </div>
          <div class="card-info">
            <span class="info-label">适用学历</span>
            <span class="info-value">{{ item.education_level }}</span>
          </div>
        </div>
        <div class="card-footer">
          <div class="deadline" :class="{ 'deadline-urgent': isUrgent(item) }">
            <span v-if="item.metadata?.deadline">
              ⏰ 截止：{{ formatTime(item.metadata.deadline) }}
              <span v-if="isUrgent(item)" class="urgent-tag">即将截止</span>
            </span>
            <span v-else>⏰ 截止时间未设置</span>
          </div>
          <el-button text type="primary" size="small">查看详情 →</el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无符合条件的政策" />

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchPolicies"
      />
    </div>

    <!-- 政策详情抽屉 -->
    <el-drawer v-model="showDetail" title="政策详情" size="500px">
      <template v-if="detailData">
        <h3 class="detail-title">{{ detailData.policy.title }}</h3>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="发布学院">{{ detailData.policy.department }}</el-descriptions-item>
          <el-descriptions-item label="适用学历">{{ detailData.policy.education_level }}</el-descriptions-item>
          <el-descriptions-item label="适用年级">{{ detailData.policy.applicable_grades?.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="项目分类">{{ detailData.policy.project_category }}</el-descriptions-item>
        </el-descriptions>

        <template v-if="detailData.metadata">
          <h4 class="section-title">申请信息</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="项目名称">{{ detailData.metadata.project_name }}</el-descriptions-item>
            <el-descriptions-item label="截止时间">
              <span :class="{ 'deadline-urgent': isUrgent(detailData.policy) }">
                {{ formatTime(detailData.metadata.deadline) }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="硬性门槛">
              {{ detailData.metadata.prerequisites?.join('；') || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="材料清单">
              <ul class="material-list">
                <li v-for="(m, i) in detailData.metadata.material_list" :key="i">{{ m }}</li>
              </ul>
            </el-descriptions-item>
            <el-descriptions-item label="评选流程">{{ detailData.metadata.review_process || '未说明' }}</el-descriptions-item>
            <el-descriptions-item label="联系方式">{{ detailData.metadata.contact_info || '未说明' }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <p class="detail-note">如需申请，请准备好材料后联系辅导员</p>
      </template>
      <el-skeleton v-else :rows="6" animated />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getStudentPolicies } from '../../api/student'
import { getPolicyDetail } from '../../api/policy'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const userName = computed(() => authStore.user?.name || '同学')

const policies = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const showDetail = ref(false)
const detailData = ref<any>(null)
const loading = ref(false)

function formatTime(t: string) {
  if (!t) return '-'
  return t.replace('T', ' ').substring(0, 16)
}

function isUrgent(item: any) {
  if (!item.metadata?.deadline) return false
  const deadline = new Date(item.metadata.deadline).getTime()
  const now = Date.now()
  const daysLeft = (deadline - now) / (1000 * 60 * 60 * 24)
  return daysLeft >= 0 && daysLeft <= 3
}

async function fetchPolicies() {
  loading.value = true
  try {
    const res = await getStudentPolicies({ page: page.value, page_size: pageSize.value })
    if (res.code === 0) {
      // 合并metadata
      const items = res.data.items
      // 逐个获取metadata
      const enriched = await Promise.all(
        items.map(async (p: any) => {
          try {
            const detail = await getPolicyDetail(p.policy_id)
            if (detail.code === 0) {
              return { ...p, metadata: detail.data.metadata }
            }
          } catch {}
          return { ...p, metadata: null }
        })
      )
      policies.value = enriched
      total.value = res.data.total
    }
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function openDetail(item: any) {
  showDetail.value = true
  detailData.value = null
  try {
    const res = await getPolicyDetail(item.policy_id)
    if (res.code === 0) {
      detailData.value = res.data
    }
  } catch {
    ElMessage.error('加载详情失败')
  }
}

onMounted(() => {
  fetchPolicies()
})
</script>

<style scoped>
.dashboard-page {
  padding: 24px;
}

.welcome-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 32px;
  color: #fff;
  margin-bottom: 24px;
}

.welcome-banner h2 {
  font-size: 24px;
  margin: 0;
  color: #fff;
}

.welcome-text {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 8px;
}

.policy-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.policy-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.policy-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.policy-card.urgent {
  border-color: #f56c6c;
  background: #fff5f5;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
  flex: 1;
  margin-right: 12px;
}

.card-body {
  margin-bottom: 12px;
}

.card-info {
  display: flex;
  font-size: 13px;
  margin-bottom: 4px;
}

.info-label {
  color: #999;
  width: 70px;
  flex-shrink: 0;
}

.info-value {
  color: #333;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}

.deadline {
  font-size: 13px;
  color: #666;
}

.deadline-urgent {
  color: #f56c6c;
  font-weight: 600;
}

.urgent-tag {
  display: inline-block;
  background: #f56c6c;
  color: #fff;
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 8px;
  margin-left: 6px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.detail-title {
  font-size: 18px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 15px;
  margin: 20px 0 12px;
  color: #1a1a2e;
}

.material-list {
  margin: 0;
  padding-left: 18px;
}

.material-list li {
  margin-bottom: 2px;
}

.detail-note {
  text-align: center;
  color: #999;
  font-size: 13px;
  margin-top: 24px;
}
</style>