import axios from 'axios'

// API basisopsætning
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Fejlhåndtering
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Fejl:', error.response ? error.response.data : error.message)
    return Promise.reject(error)
  }
)

export const healthService = {
  // Hent systemstatus
  getStatus() {
    return api.get('/health')
  }
}

export const meterService = {
  // Hent alle målere
  getAllMeters() {
    return api.get('/meters')
  },
  
  // Hent specifik måler
  getMeter(mac) {
    return api.get(`/meters/${mac}`)
  },
  
  // Hent måleraflæsninger
  getReadings(mac, limit = 200) {
    return api.get(`/meters/${mac}/readings`, { params: { limit } })
  },
  
  // Hent daglige aflæsninger
  getDailyReadings(mac, days = 30) {
    return api.get(`/meters/${mac}/daily`, { params: { days } })
  },
  
  // Opdater målernavn
  updateName(mac, name, number) {
    return api.post(`/meters/${mac}/name`, { name, number })
  },
  
  // Opdater eller opret måler med navn og nummer (nyt API)
  updateMeterInfo(mac, name, number) {
    return api.post('/meter/update', { mac, name, number })
  },
  
  // Slet måler
  deleteMeter(mac, code) {
    return api.delete(`/meters/${mac}`, { data: { code } })
  },
  
  // Tænd måler
  turnOn(mac) {
    return api.post(`/meters/${mac}/on`)
  },
  
  // Sluk måler
  turnOff(mac) {
    return api.post(`/meters/${mac}/off`)
  },
  
  // Scan efter nye målere
  scanForMeters() {
    return api.post('/scan')
  },
  
  // Test MQTT-forbindelse
  testMqttConnection() {
    return api.get('/mqtt/test')
  }
}

export default {
  health: healthService,
  meters: meterService
}
