<template>
  <div class="scan-meters">
    <div class="container">
      <h2>Søg Efter Nye Målere</h2>
      
      <div class="info-box">
        <h3>Sådan virker scanning efter nye målere</h3>
        <p>Når du starter en scanning, vil systemet:</p>
        <ol>
          <li>Søge i databasen efter målere, der har sendt data, men endnu ikke er navngivet</li>
          <li>Vise disse målere i en liste herunder, så du kan navngive dem</li>
          <li>Automatisk opdatere listen hvis nye ubenævnte målere registreres</li>
        </ol>
        <p>Scanningen sker øjeblikkeligt ved at tjekke databasen for ubenævnte målere.</p>
        <p><strong>Bemærk:</strong> For at en måler kan findes, skal den have sendt mindst én måling til systemet.</p>
      </div>
      
      <div class="scan-controls">
        <button 
          @click="startScan" 
          :disabled="loading" 
          class="btn btn-success"
        >
          {{ loading ? 'Søger...' : 'Find Ubenævnte Målere' }}
        </button>
        
        <p v-if="loading" class="scanning-info">
          <span class="pulse-dot"></span>
          Søger efter ubenævnte målere i databasen...
        </p>
      </div>
      
      <ErrorAlert 
        v-if="error" 
        :message="error" 
        @dismiss="clearError" 
      />
      
      <div v-if="foundMeters.length > 0" class="found-meters">
        <h3>Ubenævnte målere fundet ({{ foundMeters.length }})</h3>
        
        <div class="grid">
          <div v-for="meter in foundMeters" :key="meter.mac" class="meter-card new-meter">
            <div class="meter-header">
              <h4>{{ meter.name || 'Unavngivet måler' }}</h4>
              <span class="badge new">Ny</span>
              <span :class="['status-indicator', meter.status]" :title="meter.status"></span>
            </div>
            
            <div class="meter-info">
              <p><strong>MAC:</strong> {{ meter.mac }}</p>
              <p><strong>Status:</strong> {{ meter.status === 'online' ? 'Online' : 'Offline' }}</p>
              <p><strong>Sidst set:</strong> {{ formatDate(meter.sidst_set) }}</p>
              <p v-if="meter.seneste_effekt !== undefined"><strong>Seneste måling:</strong> {{ meter.seneste_effekt }} W</p>
              <p v-if="meter.antal_dage_med_data"><strong>Dage med data:</strong> {{ meter.antal_dage_med_data }}</p>
            </div>
            
            <div class="meter-actions">
              <button @click="editMeter(meter)" class="btn">Navngiv Måler</button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else-if="loading" class="empty-scan">
        <LoadingIndicator message="Søger efter ubenævnte målere..." />
      </div>
      
      <div v-else-if="hasScanned" class="empty-scan">
        <p>Ingen ubenævnte målere blev fundet i databasen.</p>
        <p>Alle målere er enten navngivet eller har endnu ikke sendt data til systemet.</p>
      </div>
    </div>
    
    <!-- Modal til navngivning af ny måler -->
    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Navngiv Ny Måler</h3>
          <button @click="closeModal" class="close-button">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label for="meter-name">Navn</label>
            <input 
              type="text" 
              id="meter-name" 
              v-model="editedMeter.name" 
              class="form-control" 
              placeholder="F.eks. 'Badevogn 12' eller 'Toilet bygning Nord'"
            />
          </div>
          
          <div class="form-group">
            <label for="meter-number">Nummer (3 cifre)</label>
            <input 
              type="text" 
              id="meter-number" 
              v-model="editedMeter.number" 
              class="form-control" 
              placeholder="F.eks. '101'" 
              maxlength="3"
              pattern="[0-9]{3}"
            />
            <small class="form-text text-muted">Angiv et unikt trecifret nummer (000-999)</small>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeModal" class="btn btn-secondary">Annuller</button>
          <button 
            @click="saveMeter" 
            class="btn btn-primary" 
            :disabled="!isValidForm"
          >
            Gem
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { mapState, mapActions, mapMutations } from 'vuex'
import ErrorAlert from '@/components/ErrorAlert.vue'
import LoadingIndicator from '@/components/LoadingIndicator.vue'
import io from 'socket.io-client'

export default {
  name: 'ScanMeters',
  components: {
    ErrorAlert,
    LoadingIndicator
  },
  setup() {
    // State
    const socket = ref(null)
    const loading = ref(false)
    const hasScanned = ref(false)
    const foundMeters = ref([])
    const showEditModal = ref(false)
    const editedMeter = ref({
      mac: '',
      name: '',
      number: ''
    })
    
    // Computed
    const isValidForm = computed(() => {
      return editedMeter.value.name && 
             editedMeter.value.name.trim() !== '' &&
             editedMeter.value.number && 
             /^\d{3}$/.test(editedMeter.value.number)
    })
    
    // Methods
    const editMeter = (meter) => {
      editedMeter.value = {
        mac: meter.mac,
        name: meter.name || '',
        number: meter.number || ''
      }
      showEditModal.value = true
    }
    
    const closeModal = () => {
      showEditModal.value = false
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'Ukendt'
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      
      return new Intl.DateTimeFormat('da-DK', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date)
    }
    
    // Lifecycle hooks
    onMounted(() => {
      // Opret socket.io forbindelse
      socket.value = io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
      })
      
      // Lyt efter nye ubenævnte målere meddelelser
      socket.value.on('new_unnamed_meters', (data) => {
        console.log('Modtog real-time opdatering om nye ubenævnte målere:', data)
        
        // Tilføj kun de nye målere til listen, som ikke allerede findes
        if (data && data.meters && data.meters.length > 0) {
          data.meters.forEach(newMeter => {
            // Check om denne måler allerede findes i listen
            const existingIndex = foundMeters.value.findIndex(m => m.mac === newMeter.mac)
            
            if (existingIndex === -1) {
              // Tilføj til listen hvis den ikke findes
              foundMeters.value.push(newMeter)
            }
          })
        }
      })
    })
    
    onBeforeUnmount(() => {
      // Luk socket.io forbindelsen
      if (socket.value) {
        socket.value.disconnect()
      }
    })
    
    return {
      loading,
      hasScanned,
      foundMeters,
      showEditModal,
      editedMeter,
      isValidForm,
      editMeter,
      closeModal,
      formatDate
    }
  },
  computed: {
    ...mapState({
      error: state => state.error
    })
  },
  methods: {
    ...mapActions([
      'scanForMeters',
      'updateMeterName'
    ]),
    ...mapMutations([
      'CLEAR_ERROR'
    ]),
    
    async startScan() {
      try {
        this.loading = true
        this.hasScanned = true
        
        // Nulstil liste ved ny scanning
        this.foundMeters = []
        
        // Kald backend API for at scanne efter ubenævnte målere
        const response = await this.scanForMeters()
        
        // Hvis der kom målere fra API'et, vis dem
        if (response && response.meters && response.meters.length > 0) {
          this.foundMeters = response.meters
        }
        
      } catch (error) {
        console.error('Fejl ved scanning efter nye målere:', error)
      } finally {
        this.loading = false
      }
    },
    
    async saveMeter() {
      if (!this.isValidForm) return
      
      try {
        // Gem måler-info i databasen
        await this.updateMeterName({
          mac: this.editedMeter.mac,
          name: this.editedMeter.name,
          number: this.editedMeter.number
        })
        
        // Fjern måler fra listen over ubenævnte målere
        const idx = this.foundMeters.findIndex(m => m.mac === this.editedMeter.mac)
        if (idx !== -1) {
          this.foundMeters.splice(idx, 1)
        }
        
        // Luk modal vinduet
        this.closeModal()
        
      } catch (error) {
        console.error('Fejl ved opdatering af målernavn:', error)
      }
    },
    
    clearError() {
      this.CLEAR_ERROR()
    }
  }
}
</script>

<style scoped>
.scan-meters {
  padding: 1rem 0;
}

h2 {
  margin-bottom: 1rem;
}

.info-box {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.info-box h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #343a40;
}

.info-box ol {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.info-box li {
  margin-bottom: 0.5rem;
}

.scan-controls {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.btn {
  padding: 0.5rem 1.5rem;
  cursor: pointer;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #218838;
}

.scanning-info {
  display: flex;
  align-items: center;
  margin-top: 1rem;
  color: #495057;
}

.pulse-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #28a745;
  margin-right: 10px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 10px rgba(40, 167, 69, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(40, 167, 69, 0);
  }
}

.found-meters {
  margin-top: 2rem;
}

.found-meters h3 {
  margin-bottom: 1rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.meter-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.meter-card.new-meter {
  border-left: 3px solid #28a745;
}

.meter-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid #eee;
}

.meter-header h4 {
  margin: 0;
  font-size: 1.1rem;
  word-break: break-word;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1;
  border-radius: 0.25rem;
}

.badge.new {
  background-color: #28a745;
  color: white;
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-left: 10px;
}

.status-indicator.online {
  background-color: #28a745;
}

.status-indicator.offline {
  background-color: #dc3545;
}

.meter-info {
  padding: 1rem;
}

.meter-info p {
  margin: 0.5rem 0;
  font-size: 0.9rem;
}

.meter-actions {
  padding: 1rem;
  border-top: 1px solid #eee;
  text-align: right;
}

.empty-scan {
  text-align: center;
  padding: 3rem 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-top: 2rem;
}

.empty-scan p {
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  color: #6c757d;
}

.close-button:hover {
  color: #343a40;
}

.modal-body {
  padding: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
}

.help-text {
  font-size: 0.85rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.modal-footer {
  padding: 1rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  border-top: 1px solid #eee;
}

@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    width: 95%;
  }
}
</style>
