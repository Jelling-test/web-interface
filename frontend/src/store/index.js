import { createStore } from 'vuex'
import io from 'socket.io-client'
import { healthService, meterService } from '@/services/api'

// Opret socket.io forbindelse
const socket = io({
  transports: ['polling', 'websocket'],
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,
  timeout: 20000
})

export default createStore({
  state: {
    // System status
    systemStatus: {
      dbConnected: false,
      mqttConnected: false
    },
    // Måler data
    meters: [],
    selectedMeter: null,
    meterReadings: [],
    dailyReadings: [],
    // Pagination
    currentPage: 1,
    itemsPerPage: 12,
    // Søgning og filtrering
    searchQuery: '',
    filterActive: false,
    // Loading states
    loading: {
      meters: false,
      readings: false,
      details: false,
      mqtt: false,
      delete: false,
      scan: false
    },
    // Socket.io status
    socketConnected: false,
    // Fejl
    error: null
  },
  
  getters: {
    // Filtrerede og søgbare målere
    filteredMeters: (state) => {
      // Filtrer først målere baseret på, om de har et navn (er navngivet)
      let filteredList = state.meters.filter(meter => meter.name && meter.name !== 'Unavngivet');
      
      // Anvend derefter aktiv-filter hvis det er aktiveret
      if (state.filterActive) {
        filteredList = filteredList.filter(meter => meter.status === 'online');
      }
      
      // Anvend søgning hvis der er en søgeforespørgsel
      if (state.searchQuery) {
        const searchLower = state.searchQuery.toLowerCase();
        filteredList = filteredList.filter(meter => 
          (meter.name && meter.name.toLowerCase().includes(searchLower)) || 
          (meter.number && meter.number.toString().includes(searchLower)) ||
          (meter.mac && meter.mac.toLowerCase().includes(searchLower))
        );
      }
      
      return filteredList;
    },
    
    // Paginerede målere
    paginatedMeters: (state, getters) => {
      const start = (state.currentPage - 1) * state.itemsPerPage
      const end = start + state.itemsPerPage
      return getters.filteredMeters.slice(start, end)
    },
    
    // Totalt antal sider
    totalPages: (state, getters) => {
      return Math.ceil(getters.filteredMeters.length / state.itemsPerPage)
    },
    
    // Aktive målere
    activeMeters: (state) => {
      return state.meters.filter(meter => meter.status === 'online')
    },
    
    // Inaktive målere
    inactiveMeters: (state) => {
      return state.meters.filter(meter => meter.status !== 'online')
    }
  },
  
  mutations: {
    // System status
    SET_SYSTEM_STATUS(state, status) {
      state.systemStatus = status
    },
    
    // Målere
    SET_METERS(state, meters) {
      state.meters = meters
    },
    
    SELECT_METER(state, meter) {
      state.selectedMeter = meter
    },
    
    SET_METER_READINGS(state, readings) {
      state.meterReadings = readings
    },
    
    SET_DAILY_READINGS(state, readings) {
      state.dailyReadings = readings
    },
    
    // Opdater en specifik måler (f.eks. ved realtidsopdatering)
    UPDATE_METER(state, updatedMeter) {
      const index = state.meters.findIndex(m => m.mac === updatedMeter.mac)
      if (index !== -1) {
        state.meters[index] = { ...state.meters[index], ...updatedMeter }
      }
      
      // Opdater også valgt måler hvis det er den samme
      if (state.selectedMeter && state.selectedMeter.mac === updatedMeter.mac) {
        state.selectedMeter = { ...state.selectedMeter, ...updatedMeter }
      }
    },
    
    // Tilføj en ny måler (f.eks. ved scanning)
    ADD_METER(state, meter) {
      // Undgå dubletter
      if (!state.meters.some(m => m.mac === meter.mac)) {
        state.meters.push(meter)
      }
    },
    
    // Pagination
    SET_CURRENT_PAGE(state, page) {
      state.currentPage = page
    },
    
    SET_ITEMS_PER_PAGE(state, count) {
      state.itemsPerPage = count
    },
    
    // Søgning og filtrering
    SET_SEARCH_QUERY(state, query) {
      state.searchQuery = query
      // Nulstil til første side ved ny søgning
      state.currentPage = 1
    },
    
    TOGGLE_FILTER_ACTIVE(state) {
      state.filterActive = !state.filterActive
    },
    
    // Loading states
    SET_LOADING(state, { type, status }) {
      state.loading[type] = status
    },
    
    // Socket status
    SET_SOCKET_CONNECTED(state, status) {
      state.socketConnected = status
    },
    
    // Fejl
    SET_ERROR(state, error) {
      state.error = error
    },
    
    CLEAR_ERROR(state) {
      state.error = null
    }
  },
  
  actions: {
    // Hent system status
    async fetchSystemStatus({ commit }) {
      try {
        commit('SET_LOADING', { type: 'system', status: true })
        const response = await healthService.getStatus()
        commit('SET_SYSTEM_STATUS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke hente systemstatus')
        console.error('Fejl ved hentning af systemstatus:', error)
        return null
      } finally {
        commit('SET_LOADING', { type: 'system', status: false })
      }
    },
    
    // Hent alle målere
    async fetchMeters({ commit }) {
      try {
        commit('SET_LOADING', { type: 'meters', status: true })
        const response = await meterService.getAllMeters()
        commit('SET_METERS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke hente målere')
        console.error('Fejl ved hentning af målere:', error)
        return []
      } finally {
        commit('SET_LOADING', { type: 'meters', status: false })
      }
    },
    
    // Hent en specifik måler
    async fetchMeter({ commit }, mac) {
      try {
        commit('SET_LOADING', { type: 'details', status: true })
        const response = await meterService.getMeter(mac)
        commit('SELECT_METER', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke hente målerdetaljer')
        console.error(`Fejl ved hentning af måler ${mac}:`, error)
        return null
      } finally {
        commit('SET_LOADING', { type: 'details', status: false })
      }
    },
    
    // Hent måleraflæsninger
    async fetchMeterReadings({ commit }, { mac, limit = 200 }) {
      try {
        commit('SET_LOADING', { type: 'readings', status: true })
        const response = await meterService.getReadings(mac, limit)
        commit('SET_METER_READINGS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke hente måleraflæsninger')
        console.error(`Fejl ved hentning af aflæsninger for måler ${mac}:`, error)
        return []
      } finally {
        commit('SET_LOADING', { type: 'readings', status: false })
      }
    },
    
    // Hent daglige aflæsninger
    async fetchDailyReadings({ commit }, { mac, days = 30 }) {
      try {
        commit('SET_LOADING', { type: 'daily', status: true })
        const response = await meterService.getDailyReadings(mac, days)
        commit('SET_DAILY_READINGS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke hente daglige aflæsninger')
        console.error(`Fejl ved hentning af daglige aflæsninger for måler ${mac}:`, error)
        return []
      } finally {
        commit('SET_LOADING', { type: 'daily', status: false })
      }
    },
    
    // Opdater målernavn
    async updateMeterName({ commit }, { mac, name, number }) {
      try {
        commit('SET_LOADING', { type: 'details', status: true })
        
        // Brug den nye API som opretter eller opdaterer måler-info
        const response = await meterService.updateMeterInfo(mac, name, number)
        
        // Tjek om der var fejl i API-responsen
        if (response.data.status === 'error') {
          commit('SET_ERROR', response.data.message || 'Kunne ikke opdatere måleren')
          return false
        }
        
        // Vis bruger-info om success
        console.log(`Måler ${name} (${mac}) blev opdateret med nummer ${number}`)
        
        // Opdater lokal state hvis response indeholder måler-data
        if (response.data.meter) {
          commit('UPDATE_METER', {
            mac: mac,
            name: name,
            number: number
          })
        }
        
        return true
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke opdatere måler i systemet')
        console.error('Fejl ved opdatering af målernavn:', error)
        return false
      } finally {
        commit('SET_LOADING', { type: 'details', status: false })
      }
    },
    
    // Slet måler
    async deleteMeter({ commit, state }, { mac, code }) {
      try {
        commit('SET_LOADING', { type: 'delete', status: true })
        await meterService.deleteMeter(mac, code)
        
        // Fjern måler fra state
        commit('SET_METERS', state.meters.filter(m => m.mac !== mac))
        
        // Hvis det er den valgte måler, nulstil valget
        if (state.selectedMeter && state.selectedMeter.mac === mac) {
          commit('SELECT_METER', null)
        }
        
        return true
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke slette måler')
        console.error(`Fejl ved sletning af måler ${mac}:`, error)
        return false
      } finally {
        commit('SET_LOADING', { type: 'delete', status: false })
      }
    },
    
    // Tænd måler
    async turnOnMeter({ commit }, mac) {
      try {
        await meterService.turnOn(mac)
        return true
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke tænde måler')
        console.error(`Fejl ved tænding af måler ${mac}:`, error)
        return false
      }
    },
    
    // Sluk måler
    async turnOffMeter({ commit }, mac) {
      try {
        await meterService.turnOff(mac)
        return true
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke slukke måler')
        console.error(`Fejl ved slukning af måler ${mac}:`, error)
        return false
      }
    },
    
    // Test MQTT-forbindelse
    async testMqttConnection({ commit }) {
      try {
        commit('SET_LOADING', { type: 'mqtt', status: true })
        const response = await meterService.testMqttConnection()
        return response.data
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke teste MQTT-forbindelse')
        console.error('Fejl ved test af MQTT-forbindelse:', error)
        return { status: 'error', message: error.message }
      } finally {
        commit('SET_LOADING', { type: 'mqtt', status: false })
      }
    },
    
    // Scan efter nye målere
    async scanForMeters({ commit }) {
      try {
        commit('SET_LOADING', { type: 'scan', status: true })
        const response = await meterService.scanForMeters()
        
        if (response.data.status === 'error') {
          commit('SET_ERROR', response.data.message || 'Kunne ikke søge efter ubenævnte målere')
          console.error('API fejl ved scanning:', response.data.error)
          return false
        }
        
        // Log resultat til konsollen
        console.log(`Fandt ${response.data.count} ubenævnte målere`)
        
        // Returnér hele response data objektet
        return response.data
      } catch (error) {
        commit('SET_ERROR', 'Kunne ikke kontakte serveren for at søge efter nye målere')
        console.error('Fejl ved scanning efter nye målere:', error)
        return false
      } finally {
        commit('SET_LOADING', { type: 'scan', status: false })
      }
    },
    
    // Opsæt socket.io lyttere
    setupSocketListeners({ commit }) {
      // Forbindelse oprettet
      socket.on('connect', () => {
        commit('SET_SOCKET_CONNECTED', true)
        console.log('Socket.io forbindelse oprettet')
      })
      
      // Forbindelse afbrudt
      socket.on('disconnect', () => {
        commit('SET_SOCKET_CONNECTED', false)
        console.log('Socket.io forbindelse afbrudt')
      })
      
      // MQTT besked modtaget
      socket.on('mqtt_message', ({ topic, payload }) => {
        console.log('MQTT besked modtaget:', topic, payload)
        
        // Håndter forskellige beskedtyper
        if (topic.includes('/status')) {
          const mac = topic.split('/')[1]
          commit('UPDATE_METER', { 
            mac, 
            status: payload.status || 'unknown',
            lastSeen: new Date().toISOString()
          })
        } else if (topic.includes('/data')) {
          const mac = topic.split('/')[1]
          
          // Opdater målerværdier
          commit('UPDATE_METER', { 
            mac, 
            lastReading: payload.value,
            lastReadingTime: new Date().toISOString()
          })
          
          // Hvis denne måler er valgt, opdater readings
          const selectedMeter = this.state.selectedMeter
          if (selectedMeter && selectedMeter.mac === mac) {
            // Tilføj ny aflæsning til grafen hvis målerdetaljerne vises
            commit('SET_METER_READINGS', [
              { timestamp: new Date().toISOString(), value: payload.value },
              ...this.state.meterReadings.slice(0, 199) // Behold kun de seneste 200
            ])
          }
        }
      })
    }
  }
})
