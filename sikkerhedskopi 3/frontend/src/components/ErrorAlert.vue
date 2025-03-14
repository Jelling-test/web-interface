<template>
  <transition name="fade">
    <div v-if="show" class="error-alert" :class="{ 'with-icon': showIcon }">
      <div v-if="showIcon" class="error-icon">
        <span>&#9888;</span>
      </div>
      <div class="error-content">
        <div class="error-message">{{ message }}</div>
        <div v-if="details" class="error-details">{{ details }}</div>
      </div>
      <button v-if="dismissable" @click="$emit('dismiss')" class="dismiss-button" aria-label="Luk">
        &times;
      </button>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'ErrorAlert',
  props: {
    show: {
      type: Boolean,
      default: true
    },
    message: {
      type: String,
      required: true
    },
    details: {
      type: String,
      default: ''
    },
    dismissable: {
      type: Boolean,
      default: true
    },
    showIcon: {
      type: Boolean,
      default: true
    }
  },
  emits: ['dismiss']
}
</script>

<style scoped>
.error-alert {
  display: flex;
  align-items: flex-start;
  background-color: #fff0f0;
  border-left: 4px solid #dc3545;
  color: #721c24;
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.error-alert.with-icon {
  padding-left: 12px;
}

.error-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  color: #dc3545;
  font-size: 1.5rem;
}

.error-content {
  flex: 1;
}

.error-message {
  font-weight: 500;
  margin-bottom: 4px;
}

.error-details {
  font-size: 0.9rem;
  opacity: 0.85;
}

.dismiss-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #721c24;
  opacity: 0.7;
  cursor: pointer;
  padding: 0 0 0 16px;
  line-height: 1;
  margin-left: 8px;
}

.dismiss-button:hover {
  opacity: 1;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
