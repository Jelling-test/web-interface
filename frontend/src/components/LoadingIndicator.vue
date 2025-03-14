<template>
  <div class="loading-container" :class="{ overlay: isOverlay, small: size === 'small' }">
    <div class="spinner" :class="{ small: size === 'small', large: size === 'large' }"></div>
    <div v-if="message" class="loading-message">{{ message }}</div>
  </div>
</template>

<script>
export default {
  name: 'LoadingIndicator',
  props: {
    isOverlay: {
      type: Boolean,
      default: false
    },
    message: {
      type: String,
      default: 'Indlæser...'
    },
    size: {
      type: String,
      default: 'medium',
      validator: value => ['small', 'medium', 'large'].includes(value)
    }
  }
}
</script>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.loading-container.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  z-index: 100;
}

.loading-container.small {
  padding: 0.5rem;
}

.spinner {
  display: inline-block;
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 123, 255, 0.2);
  border-top-color: #007bff;
  border-radius: 50%;
  animation: spin 1s ease-in-out infinite;
}

.spinner.small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

.spinner.large {
  width: 60px;
  height: 60px;
  border-width: 6px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-message {
  margin-top: 0.5rem;
  color: #555;
  font-size: 0.9rem;
  text-align: center;
}
</style>
