<template>
  <div class="placeholder">
    <el-empty :description="pageName" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pageName = computed(() => {
  const map: Record<string, string> = {
    'admin/settings': '系统配置（开发中）',
    'admin/pending': '待审批（开发中）',
    'admin/statistics': '全校统计（开发中）',
    'admin/projects': '项目管理（开发中）',
    'teacher/upload': '上传政策（开发中）',
    'teacher/pending-review': '待初审（开发中）',
    'teacher/pending-final': '待终核（开发中）',
    'teacher/statistics': '数据统计（开发中）',
    'teacher/policies': '政策管理（开发中）',
    'student/dashboard': '信息看板（开发中）',
    'student/favorites': '我的关注（开发中）',
    'student/applications': '我的申请（开发中）',
    'student/qa': '智能问答（开发中）',
  }
  return map[route.path.replace('/', '')] || '开发中'
})
</script>

<style scoped>
.placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
</style>