<template>
  <div class="meter-card" @click="$emit('click')" :class="{ offline: !isOnline }">
    <div class="meter-header">
      <h3>{{ meter.name || 'Unavngivet måler' }}</h3>
      <div class="meter-status">
        <span 
          class="status-indicator" 
          :class="{ online: isOnline, offline: !isOnline }"
        ></span>
        <span class="status-text">{{ isOnline ? 'Online' : 'Offline' }}</span>
      </div>
    </div>
    
    <div class="meter-info">
      <div class="info-row">
        <span class="info-label">Nummer:</span>
        <span class="info-value">{{ meter.number || 'Ikke tildelt' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">MAC:</span>
        <span class="info-value mac">{{ meter.mac }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Sidst set:</span>
        <span class="info-value">{{ formatDate(meter.lastSeen) }}</span>
      </div>
      <div class="info-row" v-if="hasReading">
        <span class="info-label">Seneste aflæsning:</span>
        <span class="info-value" style="display: inline-block; width: 20px;"></span>
        <span class="info-value reading">{{ meter.lastReading }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Status:</span>
        <span class="info-value power-status" v-if="meter.power === 'tændt'" style="color: #28a745; font-weight: bold;">Tændt</span>
        <span class="info-value power-status" v-else style="color: #dc3545; font-weight: bold;">Slukket</span>
      </div>
    </div>
    
    <div class="meter-footer">
      <span class="view-details">Se detaljer</span>
      <i class="arrow-icon">&#10095;</i>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MeterCard',
  props: {
    meter: {
      type: Object,
      required: true
    }
  },
  mounted() {
    console.log('Meter objekt:', this.meter)
  },
  computed: {
    isOnline() {
      return this.meter.status === 'online'
    },
    hasReading() {
      return this.meter.lastReading !== undefined && this.meter.lastReading !== null
    }
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return 'Ukendt'
      
      try {
        const date = new Date(dateString)
        return date.toLocaleString('da-DK', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (error) {
        return 'Ugyldig dato'
      }
    }
  }
}
</script>

<style scoped>
.meter-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.meter-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
}

.meter-card.offline {
  background-color: #f9f9f9;
  border-left: 3px solid #dc3545;
}

.meter-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid #eee;
}

.meter-header h3 {
  margin: 0;
  font-size: 1.1rem;
  word-break: break-word;
}

.meter-status {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-left: 0.5rem;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 5px;
}

.status-indicator.online {
  background-color: #28a745;
  box-shadow: 0 0 5px #28a745;
  animation: pulse 2s infinite;
}

.status-indicator.offline {
  background-color: #dc3545;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7);
  }
  70% {
    box-shadow: 0 0 0 5px rgba(40, 167, 69, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(40, 167, 69, 0);
  }
}

.status-text {
  font-size: 0.8rem;
  font-weight: 500;
}

.meter-info {
  flex: 1;
  padding: 1rem;
}

.info-row {
  display: flex;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.info-label {
  color: #666;
  min-width: 100px;
}

.info-value {
  font-weight: 500;
}

.info-value.mac {
  font-family: monospace;
  font-size: 0.85rem;
}

.info-value.reading {
  color: #0056b3;
  font-weight: 600;
}

.power-status {
  font-weight: bold;
}

.power-status:first-of-type {
  color: #28a745;
}

.power-status:last-of-type {
  color: #dc3545;
}

.meter-footer {
  padding: 0.75rem 1rem;
  background-color: #f8f9fa;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #eee;
}

.view-details {
  font-size: 0.9rem;
  color: #0056b3;
  font-weight: 500;
}

.arrow-icon {
  color: #0056b3;
}
</style>
