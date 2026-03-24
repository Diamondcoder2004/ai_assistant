<template>
  <div class="chat-header">
    <div v-if="sessionTitle" class="current-session-indicator">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <span>{{ sessionTitle }}</span>
    </div>
    <button @click="$emit('newChat')" class="new-chat-btn" :disabled="isLoading">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 5v14M5 12h14"/>
      </svg>
      Новый чат
    </button>
  </div>
</template>

<script setup>
defineProps({
  sessionTitle: {
    type: String,
    default: ''
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['newChat'])
</script>

<style scoped>
.chat-header {
  padding: 12px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  background: #f9fafb;
}

.current-session-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 6px 12px;
  border-radius: 6px;
}

.current-session-indicator svg {
  color: #0066cc;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #0066cc;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.new-chat-btn:hover:not(:disabled) {
  background: #0052a3;
}

.new-chat-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}
</style>
