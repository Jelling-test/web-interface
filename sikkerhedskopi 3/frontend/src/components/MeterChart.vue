<template>
  <div class="chart-container" :class="{ empty: !hasData }">
    <div v-if="loading" class="chart-loading">
      <LoadingIndicator size="small" message="Indlæser data..." />
    </div>
    
    <div v-else-if="!hasData" class="no-data">
      <p>{{ noDataMessage }}</p>
    </div>
    
    <div v-else class="chart-wrapper">
      <div class="chart-header">
        <h3>{{ title }}</h3>
        <div class="chart-controls" v-if="showControls">
          <div class="period-selector">
            <button 
              v-for="period in availablePeriods" 
              :key="period.value" 
              @click="setPeriod(period.value)"
              :class="{ active: selectedPeriod === period.value }"
              class="period-button"
            >
              {{ period.label }}
            </button>
          </div>
        </div>
      </div>
      
      <canvas ref="chartCanvas"></canvas>
      
      <div class="chart-footer" v-if="showStatistics">
        <div class="stat">
          <span class="stat-label">Minimum:</span>
          <span class="stat-value">{{ formatValue(statistics.min) }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Maksimum:</span>
          <span class="stat-value">{{ formatValue(statistics.max) }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Gennemsnit:</span>
          <span class="stat-value">{{ formatValue(statistics.avg) }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Seneste:</span>
          <span class="stat-value">{{ formatValue(statistics.latest) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import Chart from 'chart.js/auto'
import LoadingIndicator from './LoadingIndicator.vue'

export default {
  name: 'MeterChart',
  components: {
    LoadingIndicator
  },
  props: {
    // Data til grafen
    chartData: {
      type: Array,
      default: () => []
    },
    // Indlæsningsstatus
    loading: {
      type: Boolean,
      default: false
    },
    // Titel
    title: {
      type: String,
      default: 'Målerdata'
    },
    // Besked der vises når der ikke er data
    noDataMessage: {
      type: String,
      default: 'Ingen målerdata tilgængelig'
    },
    // Værdi-typen (kWh, m3, etc.)
    valueUnit: {
      type: String,
      default: ''
    },
    // Type af graf (line, bar)
    chartType: {
      type: String,
      default: 'line',
      validator: value => ['line', 'bar'].includes(value)
    },
    // Primær farve
    primaryColor: {
      type: String,
      default: '#0d6efd'
    },
    // Om grafen skal vise statistik
    showStatistics: {
      type: Boolean,
      default: true
    },
    // Om grafen skal have kontroller til tidsperioder
    showControls: {
      type: Boolean,
      default: true
    },
    // Tidsperiode
    period: {
      type: String,
      default: 'day'
    }
  },
  setup(props, { emit }) {
    const chartCanvas = ref(null)
    const chart = ref(null)
    const selectedPeriod = ref(props.period)
    
    // Tilgængelige tidsperioder
    const availablePeriods = [
      { label: 'Dag', value: 'day' },
      { label: 'Uge', value: 'week' },
      { label: 'Måned', value: 'month' }
    ]
    
    // Tjek om der er data at vise
    const hasData = computed(() => {
      return props.chartData && props.chartData.length > 0
    })
    
    // Beregn statistik
    const statistics = computed(() => {
      if (!hasData.value) {
        return {
          min: 0,
          max: 0,
          avg: 0,
          latest: 0
        }
      }
      
      // Sorter data efter tidspunkt for at sikre at vi får de rigtige værdier
      const sortedData = [...props.chartData].sort((a, b) => 
        new Date(a.timestamp) - new Date(b.timestamp)
      )
      
      const values = sortedData.map(item => parseFloat(item.value))
      return {
        min: Math.min(...values),
        max: Math.max(...values),
        avg: values.reduce((sum, value) => sum + value, 0) / values.length,
        latest: values[values.length - 1] || 0
      }
    })
    
    // Formaterede data til grafen
    const formattedData = computed(() => {
      if (!hasData.value) return {}
      
      // Sorter data efter tidspunkt
      const sortedData = [...props.chartData].sort((a, b) => 
        new Date(a.timestamp) - new Date(b.timestamp)
      )
      
      // Map data til labels og værdier
      const labels = sortedData.map(item => {
        try {
          const date = new Date(item.timestamp)
          return formatDateLabel(date, selectedPeriod.value)
        } catch (error) {
          console.error('Fejl ved formatering af dato:', error, item.timestamp)
          return 'Ugyldig dato'
        }
      })
      
      const values = sortedData.map(item => {
        const val = parseFloat(item.value)
        return isNaN(val) ? 0 : val
      })
      
      return {
        labels,
        datasets: [
          {
            label: props.title,
            data: values,
            fill: true,
            backgroundColor: `${props.primaryColor}20`, // 20 = 12% opacity
            borderColor: props.primaryColor,
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 3,
            pointBackgroundColor: props.primaryColor,
            pointBorderColor: '#fff',
            pointBorderWidth: 1
          }
        ]
      }
    })
    
    // Formater datoer baseret på tidsperioden
    const formatDateLabel = (date, period) => {
      switch (period) {
        case 'day':
          return date.toLocaleTimeString('da-DK', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })
        case 'week':
          return date.toLocaleDateString('da-DK', { 
            weekday: 'short', 
            day: 'numeric' 
          })
        case 'month':
          return date.toLocaleDateString('da-DK', { 
            day: 'numeric', 
            month: 'short' 
          })
        default:
          return date.toLocaleString('da-DK')
      }
    }
    
    // Formater værdier med enheder
    const formatValue = (value) => {
      if (value === undefined || value === null) return 'N/A'
      
      // Afrund til 2 decimaler
      const formattedValue = Math.round(value * 100) / 100
      
      // Tilføj enheder hvis angivet
      return props.valueUnit ? `${formattedValue} ${props.valueUnit}` : formattedValue.toString()
    }
    
    // Ændre tidsperiode
    const setPeriod = (period) => {
      selectedPeriod.value = period
      emit('period-change', period)
      
      // Opdater grafen hvis den eksisterer
      if (chart.value) {
        updateChart()
      }
    }
    
    // Initialiser grafen
    const initializeChart = () => {
      if (!chartCanvas.value) return
      
      // Hvis der allerede er en graf, ødelæg den
      if (chart.value) {
        chart.value.destroy()
      }
      
      // Opret ny graf
      chart.value = new Chart(chartCanvas.value, {
        type: props.chartType,
        data: formattedData.value,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              callbacks: {
                label: function(context) {
                  let label = context.dataset.label || '';
                  if (label) {
                    label += ': ';
                  }
                  if (context.parsed.y !== null) {
                    label += formatValue(context.parsed.y);
                  }
                  return label;
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              }
            },
            y: {
              beginAtZero: false,
              ticks: {
                callback: function(value) {
                  return formatValue(value);
                }
              }
            }
          }
        }
      })
    }
    
    // Opdater grafen
    const updateChart = () => {
      if (!chart.value || !formattedData.value.datasets) return
      
      chart.value.data = formattedData.value
      chart.value.update()
    }
    
    // Opryd graf ved fjernelse af komponent
    const destroyChart = () => {
      if (chart.value) {
        chart.value.destroy()
        chart.value = null
      }
    }
    
    // Livscyklus hooks
    onMounted(() => {
      if (hasData.value) {
        initializeChart()
      }
    })
    
    // Watch for data changes
    watch(
      () => props.chartData,
      (newVal) => {
        if (newVal && newVal.length > 0) {
          if (chart.value) {
            updateChart()
          } else {
            initializeChart()
          }
        }
      },
      { deep: true }
    )
    
    // Watch for period changes
    watch(
      () => selectedPeriod.value,
      () => {
        if (hasData.value) {
          updateChart()
        }
      }
    )
    
    onBeforeUnmount(() => {
      destroyChart()
    })
    
    return {
      chartCanvas,
      hasData,
      statistics,
      selectedPeriod,
      availablePeriods,
      formatValue,
      setPeriod
    }
  }
}
</script>

<style scoped>
.chart-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-container.empty {
  min-height: 300px;
  justify-content: center;
  align-items: center;
}

.chart-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  color: #6c757d;
  text-align: center;
  padding: 1rem;
}

.chart-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.chart-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #212529;
}

.chart-controls {
  display: flex;
  align-items: center;
}

.period-selector {
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #dee2e6;
}

.period-button {
  background-color: white;
  border: none;
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  border-right: 1px solid #dee2e6;
}

.period-button:last-child {
  border-right: none;
}

.period-button.active {
  background-color: #0d6efd;
  color: white;
}

.period-button:hover:not(.active) {
  background-color: #f8f9fa;
}

canvas {
  flex: 1;
  min-height: 250px;
}

.chart-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
  flex-wrap: wrap;
  border-top: 1px solid #e9ecef;
  padding-top: 1rem;
}

.stat {
  text-align: center;
  padding: 0.5rem;
  flex: 1;
  min-width: 100px;
}

.stat-label {
  display: block;
  font-size: 0.8rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 500;
  color: #212529;
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .chart-controls {
    margin-top: 1rem;
    width: 100%;
  }
  
  .period-selector {
    width: 100%;
    justify-content: space-between;
  }
  
  .period-button {
    flex: 1;
    text-align: center;
  }
  
  .chart-footer {
    flex-wrap: wrap;
  }
  
  .stat {
    min-width: 50%;
    margin-bottom: 0.5rem;
  }
}
</style>
