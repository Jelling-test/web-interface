<template>
  <div class="chart-container" :class="{ empty: !hasData }">
    <div v-if="loading" class="chart-loading">
      <div class="loading-spinner"></div>
      <p>Indlæser data...</p>
    </div>
    
    <div v-else-if="!hasData" class="no-data">
      <p>{{ noDataMessage }}</p>
    </div>
    
    <div v-else class="chart-wrapper">
      <div class="chart-header">
        <h3>{{ title }}</h3>
      </div>
      
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import Chart from 'chart.js/auto'

export default {
  name: 'MeterLineChart',
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
    // Primær farve
    primaryColor: {
      type: String,
      default: '#0d6efd'
    }
  },
  setup(props) {
    const chartCanvas = ref(null)
    const chart = ref(null)
    
    // Tjek om der er data at vise
    const hasData = computed(() => {
      return props.chartData && props.chartData.length > 0
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
          return formatDateLabel(date)
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
    
    // Formater datoer
    const formatDateLabel = (date) => {
      return date.toLocaleString('da-DK', { 
        day: 'numeric', 
        month: 'short',
        hour: '2-digit', 
        minute: '2-digit' 
      })
    }
    
    // Formater værdier med enheder
    const formatValue = (value) => {
      if (value === undefined || value === null) return 'N/A'
      
      // Afrund til 2 decimaler
      const formattedValue = Math.round(value * 100) / 100
      
      // Tilføj enheder hvis angivet
      return props.valueUnit ? `${formattedValue} ${props.valueUnit}` : formattedValue.toString()
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
        type: 'line',
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
    
    onBeforeUnmount(() => {
      destroyChart()
    })
    
    return {
      chartCanvas,
      hasData
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
  height: 300px;
  margin-bottom: 1rem;
}

.chart-container.empty {
  min-height: 300px;
  justify-content: center;
  align-items: center;
}

.chart-loading {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 300px;
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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 1rem;
}

.chart-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
}

canvas {
  flex: 1;
}
</style>
