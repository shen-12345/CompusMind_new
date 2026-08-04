<template>
  <div class="agent-container">
    <!-- 悬浮按钮 -->
    <el-button
      v-if="!visible"
      class="agent-float-btn"
      type="primary"
      circle
      @click="visible = true"
      title="智能问答 (Ctrl+K)"
    >
      <el-icon style="font-size: 22px;"><ChatDotSquare /></el-icon>
    </el-button>

    <!-- 对话窗口 -->
    <div v-if="visible" class="agent-dialog">
      <!-- 头部 -->
      <div class="agent-header">
        <span>💬 智能问答</span>
        <div class="agent-header-actions">
          <el-button link size="small" @click="clearChat" style="color: #fff;">清空</el-button>
          <el-button link size="small" @click="visible = false" style="color: #fff; font-size: 16px;">✕</el-button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="agent-messages" ref="messagesRef">
        <div v-for="(msg, i) in messages" :key="i" class="message-row" :class="msg.role">
          <div class="message-avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
          <div class="message-bubble">
            <div class="message-text">{{ msg.content }}</div>
            <div v-if="msg.sources?.length" class="message-sources">
              <div v-for="(s, j) in msg.sources" :key="j" class="source-tag">
                📄 {{ s.title }}
              </div>
            </div>
          </div>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="message-row assistant">
          <div class="message-avatar">AI</div>
          <div class="message-bubble">
            <div class="typing-dots">
              <span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="agent-input-area">
        <el-input
          v-model="inputText"
          placeholder="输入您的问题..."
          :disabled="loading"
          @keyup.enter="sendMessage"
          size="large"
        >
          <template #append>
            <el-button :disabled="loading || !inputText.trim()" @click="sendMessage" type="primary">
              发送
            </el-button>
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotSquare } from '@element-plus/icons-vue'
import { askQuestion } from '../api/agent'

const visible = ref(false)
const loading = ref(false)
const inputText = ref('')
const messagesRef = ref<HTMLElement | null>(null)

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: { policy_id: number; title: string }[]
}

const messages = ref<Message[]>([
  { role: 'assistant', content: '你好！我是校事通智能助手，可以帮你解答政策相关问题。例如：\n- "这个奖学金需要什么材料？"\n- "什么时候截止？"\n- "申请条件是什么？"' },
])

let history: { role: string; content: string }[] = []

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  history.push({ role: 'user', content: text })
  loading.value = true
  scrollToBottom()

  try {
    const res = await askQuestion(text, history.slice(-10))
    if (res.code === 0) {
      messages.value.push({
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources,
      })
      history.push({ role: 'assistant', content: res.data.answer })

      // 如果历史超过 10 轮，压缩
      if (history.length > 20) {
        history = history.slice(-10)
      }
    } else {
      messages.value.push({ role: 'assistant', content: res.message || '服务异常，请稍后重试' })
    }
  } catch (err: any) {
    messages.value.push({ role: 'assistant', content: '网络异常，请检查连接后重试' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function clearChat() {
  messages.value = [{ role: 'assistant', content: '已清空对话，有什么可以帮您的？' }]
  history = []
}

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    visible.value = !visible.value
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.agent-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
}

.agent-float-btn {
  width: 56px;
  height: 56px;
  font-size: 24px;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.4);
}

.agent-dialog {
  width: 400px;
  height: 560px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.agent-header {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
  font-weight: 600;
}

.agent-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.agent-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fb;
}

.message-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.message-row.user .message-avatar {
  background: #409eff;
  color: #fff;
}

.message-row.assistant .message-avatar {
  background: #7c3aed;
  color: #fff;
}

.message-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
}

.message-row.user .message-bubble {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-row.assistant .message-bubble {
  background: #fff;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-sources {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.source-tag {
  font-size: 11px;
  color: #7c3aed;
  background: #f3e8ff;
  padding: 2px 8px;
  border-radius: 4px;
}

.typing-dots {
  font-size: 24px;
  color: #999;
  letter-spacing: 2px;
}

.agent-input-area {
  padding: 12px;
  border-top: 1px solid #e8e8e8;
  background: #fff;
}
</style>