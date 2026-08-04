<template>
  <div class="users-page">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名/姓名"
          clearable
          style="width: 240px"
          @clear="fetchUsers"
          @keyup.enter="fetchUsers"
        />
        <el-select
          v-model="filterRole"
          placeholder="全部角色"
          clearable
          style="width: 130px"
          @change="fetchUsers"
        >
          <el-option label="超级管理员" value="super_admin" />
          <el-option label="校级管理员" value="admin" />
          <el-option label="辅导员" value="teacher" />
          <el-option label="学生" value="student" />
        </el-select>
        <el-select
          v-model="filterActive"
          placeholder="全部状态"
          clearable
          style="width: 130px"
          @change="fetchUsers"
        >
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="showCreateDialog = true">
          + 创建用户
        </el-button>
      </div>
    </div>

    <!-- 用户列表表格 -->
    <el-table :data="users" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="roleTagType(row.role)" size="small">
            {{ roleLabel(row.role) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="department" label="学院" min-width="140" />
      <el-table-column prop="education_level" label="学历" width="70" />
      <el-table-column prop="grade" label="年级" width="70" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login" label="最后登录" width="170">
        <template #default="{ row }">
          {{ row.last_login ? formatTime(row.last_login) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button
            link
            :type="row.is_active ? 'warning' : 'success'"
            size="small"
            @click="handleToggleActive(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="fetchUsers"
        @size-change="fetchUsers"
      />
    </div>

    <!-- 创建用户弹窗 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建用户"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="学号/工号" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="createForm.name" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option label="学生" value="student" />
            <el-option label="辅导员" value="teacher" />
            <el-option label="校级管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="学院" prop="department">
          <el-input v-model="createForm.department" />
        </el-form-item>
        <el-form-item label="学历" prop="education_level" v-if="createForm.role === 'student'">
          <el-select v-model="createForm.education_level" style="width: 100%">
            <el-option label="本科" value="本科" />
            <el-option label="硕士" value="硕士" />
            <el-option label="博士" value="博士" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级" prop="grade" v-if="createForm.role === 'student'">
          <el-input v-model="createForm.grade" placeholder="如 2024" />
        </el-form-item>
        <el-form-item label="管辖范围" prop="admin_scope" v-if="createForm.role === 'admin'">
          <el-input v-model="createForm.admin_scope" placeholder="如 学生奖励" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 创建成功弹窗（展示初始密码） -->
    <el-dialog v-model="showPasswordDialog" title="用户创建成功" width="400px" :close-on-click-modal="false">
      <p>初始密码为：</p>
      <div class="password-box">
        <code>{{ newUserPassword }}</code>
        <el-button link type="primary" @click="copyPassword">复制</el-button>
      </div>
      <p class="password-tip">请提醒用户首次登录后修改密码。</p>
      <template #footer>
        <el-button type="primary" @click="showPasswordDialog = false">我知道了</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户弹窗 -->
    <el-dialog v-model="showEditDialog" title="编辑用户" width="480px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="用户名">
          <span>{{ editForm.username }}</span>
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="学院" prop="department">
          <el-input v-model="editForm.department" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleEditSubmit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, createUser, updateUser, toggleUserActive } from '../../api/admin/users'
import type { FormInstance, FormRules } from 'element-plus'
import type { UserItem } from '../../api/admin/users'

// 列表数据
const users = ref<UserItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const searchKeyword = ref('')
const filterRole = ref('')
const filterActive = ref<boolean | ''>('')

// 角色标签
// 当前登录用户信息
const currentUserRole = localStorage.getItem('user_role') || ''
let currentUserId = 0
try {
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
  currentUserId = userInfo.user_id || 0
} catch {}

function roleLabel(role: string) {
  const map: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '校级管理员',
    teacher: '辅导员',
    student: '学生',
  }
  return map[role] || role
}

function roleTagType(role: string) {
  const map: Record<string, string> = {
    super_admin: 'danger',
    admin: 'warning',
    teacher: 'primary',
    student: 'success',
  }
  return map[role] || 'info'
}

function formatTime(t: string) {
  return t.replace('T', ' ').substring(0, 19)
}

// 获取用户列表
async function fetchUsers() {
  loading.value = true
  try {
    const res = await getUsers({
      page: page.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value || undefined,
      role: filterRole.value || undefined,
      is_active: filterActive.value === '' ? undefined : filterActive.value,
    })
    if (res.code === 0) {
      users.value = res.data.items
      total.value = res.data.total
    }
  } catch (err: any) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 创建用户
const showCreateDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  username: '',
  name: '',
  role: 'student',
  department: '',
  education_level: '本科',
  grade: '',
  admin_scope: '',
  email: '',
})
const createRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /^\d+$/, message: '学号只能包含数字', trigger: ['blur', 'change'] },
    { min: 3, max: 50, message: '学号长度 3-50 位', trigger: ['blur', 'change'] },
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  department: [{ required: true, message: '请输入学院', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }],
}

// 编辑表单校验
const editRules: FormRules = {
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }],
}

// 创建成功弹窗
const showPasswordDialog = ref(false)
const newUserPassword = ref('')

async function handleCreate() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return
  createLoading.value = true
  try {
    const res = await createUser({
      username: createForm.username,
      name: createForm.name,
      role: createForm.role,
      department: createForm.department,
      education_level: createForm.role === 'student' ? createForm.education_level : undefined,
      grade: createForm.role === 'student' ? createForm.grade : undefined,
      admin_scope: createForm.role === 'admin' ? createForm.admin_scope : undefined,
      email: createForm.email || undefined,
    })
    if (res.code === 0) {
      newUserPassword.value = res.data.default_password
      showCreateDialog.value = false
      showPasswordDialog.value = true
      // 重置表单
      createForm.username = ''
      createForm.name = ''
      createForm.role = 'student'
      createForm.department = ''
      createForm.education_level = '本科'
      createForm.grade = ''
      createForm.admin_scope = ''
      createForm.email = ''
      fetchUsers()
    } else {
      ElMessage.error(res.message)
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '创建失败')
  } finally {
    createLoading.value = false
  }
}

function copyPassword() {
  navigator.clipboard.writeText(newUserPassword.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

// 编辑用户
const showEditDialog = ref(false)
const editLoading = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  user_id: 0,
  username: '',
  name: '',
  department: '',
  email: '',
})

function handleEdit(row: UserItem) {
  editForm.user_id = row.user_id
  editForm.username = row.username
  editForm.name = row.name
  editForm.department = row.department
  editForm.email = row.email || ''
  showEditDialog.value = true
}

async function handleEditSubmit() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return
  editLoading.value = true
  try {
    const res = await updateUser(editForm.user_id, {
      name: editForm.name,
      department: editForm.department,
      email: editForm.email || undefined,
    })
    if (res.code === 0) {
      ElMessage.success('更新成功')
      showEditDialog.value = false
      fetchUsers()
    } else {
      ElMessage.error(res.message)
    }
  } catch (err: any) {
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

// 启用/禁用
async function handleToggleActive(row: UserItem) {
  const action = row.is_active ? '禁用' : '启用'

  // 前端提前检查：不能禁用自己
  if (currentUserId === row.user_id) {
    ElMessage.warning('不能禁用自己的账号')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定${action}账号 "${row.name}" 吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const res = await toggleUserActive(row.user_id)
    if (res.code === 0) {
      ElMessage.success(`${action}成功`)
      fetchUsers()
    } else {
      ElMessage.error(res.message || '操作失败')
    }
  } catch {
    // 用户取消对话框，不处理
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.users-page {
  padding: 24px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.password-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 6px;
  margin: 8px 0;
}

.password-box code {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #1a1a2e;
}

.password-tip {
  color: #888;
  font-size: 13px;
}
</style>