<template>
  <div class="meter-detail">
    <div v-if="loading.details" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Indlæser målerdetaljer...</p>
    </div>
    
    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="CLEAR_ERROR" class="btn btn-primary">Prøv igen</button>
    </div>
    
    <div v-else-if="selectedMeter" class="meter-info-container">
      <div class="meter-header">
        <h1>{{ selectedMeter.info.name || 'Unavngivet måler' }}</h1>
        <div class="meter-status">
          <span 
            class="status-indicator" 
            :class="{ 'online': selectedMeter.status.status === 'Tændt', 'offline': selectedMeter.status.status !== 'Tændt' }"
          ></span>
          <span class="status-text" :style="{ color: selectedMeter.status.status === 'Tændt' ? 'green' : 'red' }">
            {{ selectedMeter.status.status }}
          </span>
        </div>
      </div>
      
      <div class="meter-details">
        <div class="detail-item">
          <span class="detail-label">Måler nummer:</span>
          <span class="detail-value">{{ selectedMeter.info.nummer || 'Ikke angivet' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">MAC-adresse:</span>
          <span class="detail-value">{{ selectedMeter.mac }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Sidst set:</span>
          <span class="detail-value">{{ formatDate(selectedMeter.status.oprettet || selectedMeter.status.tidspunkt) || 'Ukendt' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Seneste aflæsning:</span>
          <span class="detail-value">{{ selectedMeter.last_reading.totalkwh || 'Ingen aflæsning' }} kWh</span>
        </div>
      </div>
      
      <div class="meter-actions">
        <button @click="showEditModal = true" class="btn btn-primary">Rediger</button>
        <button @click="turnOn" class="btn btn-success" :disabled="controlLoading === 'on'">
          <span v-if="controlLoading === 'on'" class="loading-spinner-small"></span>
          Tænd
        </button>
        <button @click="turnOff" class="btn btn-danger" :disabled="controlLoading === 'off'">
          <span v-if="controlLoading === 'off'" class="loading-spinner-small"></span>
          Sluk
        </button>
        <button @click="testMqtt" class="btn btn-info" :disabled="mqttTestLoading">
          <span v-if="mqttTestLoading" class="loading-spinner-small"></span>
          Test MQTT
        </button>
        <div v-if="controlSuccess" class="control-success">{{ controlSuccess }}</div>
        <div v-if="mqttTestResult" class="mqtt-test-result" :class="{ 'mqtt-success': mqttTestResult.status === 'success', 'mqtt-error': mqttTestResult.status === 'error' }">
          {{ mqttTestResult.message }}
        </div>
      </div>
      
      <div class="row">
        <div class="col-12">
          <div class="card mb-4">
            <div class="card-header">
              <h5>Målerdata</h5>
            </div>
            <div class="card-body">
              <!-- Seneste aflæsninger -->
              <div v-if="loading.readings && !meterReadings.length" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Indlæser...</span>
                </div>
                <p class="mt-2">Henter seneste aflæsninger...</p>
              </div>
              <div v-else-if="!meterReadings.length" class="text-center py-4">
                <p>Ingen seneste aflæsninger tilgængelige</p>
              </div>
              <div v-else>
                <MeterLineChart 
                  :chartData="formattedReadingsData" 
                  :loading="loading.readings"
                  title="Seneste aflæsninger"
                  valueUnit="kWh"
                />
              </div>

              <!-- Daglige målinger -->
              <div v-if="loading.daily && !dailyReadings.length" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Indlæser...</span>
                </div>
                <p class="mt-2">Henter daglige målinger...</p>
              </div>
              <div v-else-if="!dailyReadings.length" class="text-center py-4">
                <p>Ingen daglige målinger tilgængelige</p>
              </div>
              <div v-else>
                <MeterLineChart 
                  :chartData="formattedDailyData" 
                  :loading="loading.daily"
                  title="Daglige målinger"
                  valueUnit="kWh"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="no-meter-message">
      <p>Ingen målerdata fundet. Vend tilbage til oversigten og prøv igen.</p>
      <router-link to="/" class="btn btn-primary">Tilbage til oversigten</router-link>
    </div>
    
    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal-container">
        <div class="modal-header">
          <h3>Rediger måler</h3>
          <button @click="showEditModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="meterName">Navn:</label>
            <input 
              type="text" 
              id="meterName" 
              v-model="editForm.name" 
              class="form-control" 
              placeholder="Indtast målernavn"
            >
          </div>
          <div class="form-group">
            <label for="meterNumber">Nummer (3 cifre):</label>
            <input 
              type="text" 
              id="meterNumber" 
              v-model="editForm.number" 
              class="form-control" 
              placeholder="Indtast målernummer (f.eks. 123)"
              maxlength="3"
            >
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showEditModal = false" class="btn btn-secondary">Annuller</button>
          <button @click="updateMeter" class="btn btn-primary" :disabled="!isValidForm">Gem</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapMutations } from 'vuex'
import MeterLineChart from '@/components/MeterLineChart.vue'

export default {
  name: 'MeterDetail',
  components: {
    MeterLineChart
  },
  props: {
    mac: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      showEditModal: false,
      editForm: { name: '', number: '' },
      selectedLimit: 200,
      selectedDays: 30,
      controlLoading: null,
      controlSuccess: null,
      mqttTestLoading: false,
      mqttTestResult: null
    }
  },
  computed: {
    selectedMeter() {
      return this.$store.state.selectedMeter
    },
    meterReadings() {
      return this.$store.state.meterReadings
    },
    dailyReadings() {
      return this.$store.state.dailyReadings
    },
    loading() {
      return this.$store.state.loading
    },
    error() {
      return this.$store.state.error
    },
    isValidForm() {
      const nameValid = this.editForm.name && this.editForm.name.trim().length > 0
      const numberValid = /^\d{3}$/.test(this.editForm.number)
      return nameValid && numberValid
    },
    formattedReadingsData() {
      if (!this.meterReadings || this.meterReadings.length === 0) return []
      
      // Konverter alle aflæsninger til det format, som MeterChart forventer
      return this.meterReadings.map(reading => ({
        timestamp: reading.oprettet || reading.tidspunkt,
        value: parseFloat(reading.totalkwh)
      }))
    },
    formattedDailyData() {
      if (!this.dailyReadings || this.dailyReadings.length === 0) return []
      
      // Konverter alle daglige aflæsninger til det format, som MeterChart forventer
      return this.dailyReadings.map(reading => ({
        timestamp: reading.dato || reading.date,
        value: parseFloat(reading.totalKwh)
      }))
    }
  },
  methods: {
    ...mapActions([
      'updateMeterName',
      'turnOnMeter',
      'turnOffMeter',
      'testMqttConnection',
      'fetchMeter',
      'fetchMeterReadings',
      'fetchDailyReadings'
    ]),
    ...mapMutations([
      'CLEAR_ERROR'
    ]),
    
    formatDate(dateString) {
      if (!dateString) return 'Ukendt'
      
      try {
        // Konverter strengen til et Date-objekt
        const date = new Date(dateString)
        
        // Ingen tidszone-justering - lad browseren håndtere dette korrekt
        
        // Formater dag, måned, år
        const day = date.getDate().toString().padStart(2, '0')
        const month = (date.getMonth() + 1).toString().padStart(2, '0')
        const year = date.getFullYear()
        
        // Formater timer og minutter
        const hours = date.getHours().toString().padStart(2, '0')
        const minutes = date.getMinutes().toString().padStart(2, '0')
        
        // Sammensæt det formaterede resultat
        return `${day}.${month}.${year}, ${hours}:${minutes}`
      } catch (e) {
        console.error('Fejl ved formatering af dato:', e)
        return 'Ukendt format'
      }
    },
    
    formatDateTime(dateString) {
      if (!dateString) return 'Ukendt'
      
      try {
        // Konverter strengen til et Date-objekt
        const date = new Date(dateString)
        
        // Ingen tidszone-justering - lad browseren håndtere dette korrekt
        
        // Formater dag, måned, år
        const day = date.getDate().toString().padStart(2, '0')
        const month = (date.getMonth() + 1).toString().padStart(2, '0')
        const year = date.getFullYear()
        
        // Formater timer, minutter og sekunder
        const hours = date.getHours().toString().padStart(2, '0')
        const minutes = date.getMinutes().toString().padStart(2, '0')
        const seconds = date.getSeconds().toString().padStart(2, '0')
        
        // Sammensæt det formaterede resultat
        return `${day}.${month}.${year}, ${hours}:${minutes}:${seconds}`
      } catch (e) {
        console.error('Fejl ved formatering af dato og tid:', e)
        return 'Ukendt format'
      }
    },
    
    async updateMeter() {
      if (!this.isValidForm) return
      
      const success = await this.updateMeterName({
        mac: this.mac,
        name: this.editForm.name,
        number: this.editForm.number
      })
      
      if (success) {
        this.showEditModal = false
      }
    },
    
    async turnOn() {
      this.controlLoading = 'on'
      this.controlSuccess = null
      
      const success = await this.turnOnMeter(this.mac)
      
      this.controlLoading = null
      if (success) {
        this.controlSuccess = 'Måler tændt!'
        
        // Opdater status direkte i komponenten
        if (this.selectedMeter) {
          this.selectedMeter.status.status = 'Tændt'
          this.selectedMeter.status.oprettet = new Date().toISOString()
          this.selectedMeter.status.tidspunkt = new Date().toISOString() // Behold for kompatibilitet
        }
        
        setTimeout(() => { this.controlSuccess = null }, 3000)
      }
    },
    
    async turnOff() {
      this.controlLoading = 'off'
      this.controlSuccess = null
      
      const success = await this.turnOffMeter(this.mac)
      
      this.controlLoading = null
      if (success) {
        this.controlSuccess = 'Måler slukket!'
        
        // Opdater status direkte i komponenten
        if (this.selectedMeter) {
          this.selectedMeter.status.status = 'Slukket'
          this.selectedMeter.status.oprettet = new Date().toISOString()
          this.selectedMeter.status.tidspunkt = new Date().toISOString() // Behold for kompatibilitet
        }
        
        setTimeout(() => { this.controlSuccess = null }, 3000)
      }
    },
    
    async testMqtt() {
      this.mqttTestLoading = true
      this.mqttTestResult = null
      
      const result = await this.testMqttConnection()
      
      this.mqttTestLoading = false
      this.mqttTestResult = result
      
      // Skjul resultatet efter 5 sekunder
      setTimeout(() => {
        this.mqttTestResult = null
      }, 5000)
    }
  },
  async created() {
    this.CLEAR_ERROR()
    
    // Hent målerdata når komponenten oprettes
    await this.fetchMeter(this.mac)
    
    // Hent måleraflæsninger med den valgte grænse
    await this.fetchMeterReadings({
      mac: this.mac,
      limit: this.selectedLimit
    })
    
    // Hent daglige aflæsninger for det valgte antal dage
    await this.fetchDailyReadings({
      mac: this.mac,
      days: this.selectedDays
    })
    
    // Initialiser formularen med de aktuelle værdier
    if (this.selectedMeter && this.selectedMeter.info) {
      this.editForm.name = this.selectedMeter.info.name || ''
      this.editForm.number = this.selectedMeter.info.nummer || ''
    }
  }
}
</script>

<style scoped>
  .meter-detail {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
  }

  .loading-spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin-bottom: 10px;
  }

  .loading-spinner-small {
    display: inline-block;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #fff;
    border-radius: 50%;
    width: 12px;
    height: 12px;
    animation: spin 1s linear infinite;
    margin-right: 5px;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 20px;
    border-radius: 5px;
    text-align: center;
    margin: 20px 0;
  }

  .meter-info-container {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 20px;
  }

  .meter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    border-bottom: 1px solid #eee;
    padding-bottom: 15px;
  }

  .meter-header h1 {
    margin: 0;
    font-size: 24px;
    color: #333;
  }

  .meter-status {
    display: flex;
    align-items: center;
  }

  .status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
  }

  .status-indicator.online {
    background-color: #28a745;
  }

  .status-indicator.offline {
    background-color: #dc3545;
  }

  .status-text {
    font-weight: bold;
  }

  .meter-details {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
  }

  .detail-item {
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: 5px;
  }

  .detail-label {
    font-weight: bold;
    color: #666;
    margin-right: 10px;
  }

  .detail-value {
    color: #333;
  }

  .meter-actions {
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
  }

  .btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.2s;
  }

  .btn-primary {
    background-color: #007bff;
    color: white;
  }

  .btn-primary:hover {
    background-color: #0069d9;
  }

  .btn-danger {
    background-color: #dc3545;
    color: white;
  }

  .btn-danger:hover {
    background-color: #c82333;
  }

  .btn-success {
    background-color: #28a745;
    color: white;
  }

  .btn-success:hover {
    background-color: #218838;
  }

  .btn-info {
    background-color: #17a2b8;
    color: white;
  }

  .btn-info:hover {
    background-color: #138496;
  }

  .btn-warning {
    background-color: #ffc107;
    color: #212529;
  }

  .btn-warning:hover {
    background-color: #e0a800;
  }

  .btn-secondary {
    background-color: #6c757d;
    color: white;
  }

  .btn-secondary:hover {
    background-color: #5a6268;
  }

  .btn:disabled {
    opacity: 0.65;
    cursor: not-allowed;
  }

  .control-success {
    color: #28a745;
    font-weight: bold;
    margin-left: 10px;
  }

  .mqtt-test-result {
    margin-left: 10px;
    font-weight: bold;
    padding: 5px 10px;
    border-radius: 4px;
  }

  .mqtt-success {
    color: #28a745;
  }

  .mqtt-error {
    color: #dc3545;
  }

  .data-sections {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
  }

  .data-section {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 20px;
  }

  .data-section h3 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #333;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
  }

  .data-content {
    min-height: 200px;
  }

  .no-data-message {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 150px;
    color: #6c757d;
    font-style: italic;
  }

  .no-meter-message {
    text-align: center;
    padding: 40px;
    background-color: #f8f9fa;
    border-radius: 8px;
    margin: 20px 0;
  }

  a {
    text-decoration: none;
    color: inherit;
  }

  /* Modal styles */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .modal-container {
    background-color: white;
    border-radius: 8px;
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    border-bottom: 1px solid #eee;
  }

  .modal-header h3 {
    margin: 0;
    color: #333;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #666;
  }

  .close-btn:hover {
    color: #333;
  }

  .modal-body {
    padding: 20px;
  }

  .modal-footer {
    padding: 15px 20px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .form-group {
    margin-bottom: 15px;
  }

  .form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    color: #555;
  }

  .form-control {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
  }

  .form-control:focus {
    border-color: #007bff;
    outline: none;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
  }
</style>
