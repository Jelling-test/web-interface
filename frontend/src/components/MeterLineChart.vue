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
      
      <apexchart
        type="line"
        height="300"
        :options="chartOptions"
        :series="chartSeries"
      ></apexchart>
    </div>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

export default {
  name: 'MeterLineChart',
  components: {
    apexchart: VueApexCharts
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
    // Primær farve
    primaryColor: {
      type: String,
      default: '#0d6efd'
    }
  },
  setup(props) {
    // Tjek om der er data at vise
    const hasData = computed(() => {
      return props.chartData && props.chartData.length > 0
    })
    
    // Formater datoer
    const formatDateLabel = (dateStr) => {
      try {
        const date = new Date(dateStr)
        return date.toLocaleString('da-DK', { 
          day: 'numeric', 
          month: 'short',
          hour: '2-digit', 
          minute: '2-digit' 
        })
      } catch (error) {
        console.error('Fejl ved formatering af dato:', error, dateStr)
        return 'Ugyldig dato'
      }
    }
    
    // Formaterede data til grafen - series til ApexCharts
    const chartSeries = computed(() => {
      if (!hasData.value) return []
      
      // Sorter data efter tidspunkt
      const sortedData = [...props.chartData].sort((a, b) => 
        new Date(a.timestamp) - new Date(b.timestamp)
      )
      
      // Map data til værdier
      const values = sortedData.map(item => {
        const val = parseFloat(item.value)
        return isNaN(val) ? 0 : val
      })
      
      return [{
        name: props.title,
        data: values
      }]
    })
    
    // Generér labels (x-axis kategorier) for grafen
    const chartLabels = computed(() => {
      if (!hasData.value) return []
      
      // Sorter data efter tidspunkt
      const sortedData = [...props.chartData].sort((a, b) => 
        new Date(a.timestamp) - new Date(b.timestamp)
      )
      
      // Map data til labels
      return sortedData.map(item => formatDateLabel(item.timestamp))
    })
    
    // Chart options for ApexCharts
    const chartOptions = computed(() => {
      return {
        chart: {
          type: 'line',
          height: 300,
          toolbar: {
            show: false
          },
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800
          }
        },
        colors: [props.primaryColor],
        stroke: {
          curve: 'smooth',
          width: 2
        },
        fill: {
          type: 'gradient',
          gradient: {
            shade: 'light',
            type: 'vertical',
            shadeIntensity: 0.2,
            opacityFrom: 0.7,
            opacityTo: 0.2
          }
        },
        markers: {
          size: 4,
          colors: [props.primaryColor],
          strokeColors: '#fff',
          strokeWidth: 2
        },
        tooltip: {
          x: {
            formatter: function(val) {
              return chartLabels.value[val-1] || ''
            }
          },
          y: {
            formatter: function(val) {
              return props.valueUnit ? `${val} ${props.valueUnit}` : val
            }
          }
        },
        xaxis: {
          categories: chartLabels.value,
          labels: {
            rotate: -45,
            style: {
              fontSize: '12px'
            }
          }
        },
        yaxis: {
          labels: {
            formatter: function(val) {
              const formattedValue = Math.round(val * 100) / 100
              return props.valueUnit ? `${formattedValue} ${props.valueUnit}` : formattedValue
            }
          }
        },
        grid: {
          borderColor: '#e0e0e0',
          strokeDashArray: 5
        },
        responsive: [{
          breakpoint: 576,
          options: {
            chart: {
              height: 250
            },
            xaxis: {
              labels: {
                rotate: -90
              }
            }
          }
        }]
      }
    })
    
    onMounted(() => {
      // ApexCharts håndterer automatisk opdateringer, så vi behøver ikke manuel initialisering eller opdatering
    })
    
    return {
      hasData,
      chartOptions,
      chartSeries
    }
  }
}
</script>

<style scoped>
.chart-container {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 16px;
  margin-bottom: 20px;
  height: 350px;
  position: relative;
}

.chart-container.empty {
  height: auto;
  min-height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.chart-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6c757d;
  text-align: center;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 3px solid #0d6efd;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

.chart-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6c757d;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
