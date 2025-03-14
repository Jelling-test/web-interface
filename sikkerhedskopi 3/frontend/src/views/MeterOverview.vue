<template>
  <div class="meter-overview">
    <div class="container">
      <div class="actions-bar">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            @input="onSearch" 
            placeholder="Søg efter navn, nummer eller MAC-adresse" 
            class="form-control" 
          />
          <button @click="clearSearch" v-if="searchQuery" class="btn">Ryd</button>
        </div>
        
        <div class="filter-toggle">
          <label>
            <input type="checkbox" v-model="showOnlyActive" @change="toggleActiveFilter">
            Vis kun aktive målere
          </label>
        </div>
      </div>
      
      <LoadingIndicator 
        v-if="loading.meters" 
        message="Indlæser målere..." 
      />
      
      <ErrorAlert 
        v-else-if="error" 
        :message="error" 
        @dismiss="clearError" 
      />
      
      <div v-else-if="paginatedMeters.length === 0" class="empty-state">
        <h3>Ingen målere fundet</h3>
        <p v-if="searchQuery">Prøv at søge efter noget andet</p>
        <p v-else>Der er ikke registreret nogen målere endnu</p>
        <router-link to="/scan" class="btn">Søg efter nye målere</router-link>
      </div>
      
      <div v-else>
        <div class="meter-stats">
          <div class="stat-box">
            <h3>{{ filteredMeters.length }}</h3>
            <p>Målere i alt</p>
          </div>
          <div class="stat-box active">
            <h3>{{ activeMeters.length }}</h3>
            <p>Aktive målere</p>
          </div>
          <div class="stat-box inactive">
            <h3>{{ inactiveMeters.length }}</h3>
            <p>Inaktive målere</p>
          </div>
        </div>
        
        <div class="grid">
          <MeterCard 
            v-for="meter in paginatedMeters" 
            :key="meter.mac" 
            :meter="meter" 
            @click="viewMeterDetails(meter)"
          />
        </div>
        
        <PaginationControls
          v-if="totalPages > 1"
          :current-page="currentPage"
          :total-pages="totalPages"
          :items-per-page="itemsPerPage"
          @page-change="onPageChange"
          @items-per-page-change="onItemsPerPageChange"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapMutations, mapActions } from 'vuex'
import MeterCard from '@/components/MeterCard.vue'
import LoadingIndicator from '@/components/LoadingIndicator.vue'
import ErrorAlert from '@/components/ErrorAlert.vue'
import PaginationControls from '@/components/PaginationControls.vue'

export default {
  name: 'MeterOverview',
  components: {
    MeterCard,
    LoadingIndicator,
    ErrorAlert,
    PaginationControls
  },
  data() {
    return {
      showOnlyActive: false
    }
  },
  computed: {
    ...mapState([
      'meters',
      'currentPage',
      'itemsPerPage',
      'searchQuery',
      'loading',
      'error'
    ]),
    ...mapGetters([
      'filteredMeters',
      'paginatedMeters',
      'totalPages',
      'activeMeters',
      'inactiveMeters'
    ])
  },
  methods: {
    ...mapMutations([
      'SET_CURRENT_PAGE',
      'SET_ITEMS_PER_PAGE',
      'SET_SEARCH_QUERY',
      'TOGGLE_FILTER_ACTIVE',
      'CLEAR_ERROR'
    ]),
    ...mapActions([
      'fetchMeters'
    ]),
    
    onSearch() {
      this.SET_SEARCH_QUERY(this.searchQuery)
    },
    
    clearSearch() {
      this.SET_SEARCH_QUERY('')
      this.searchQuery = ''
    },
    
    toggleActiveFilter() {
      this.TOGGLE_FILTER_ACTIVE()
    },
    
    onPageChange(page) {
      this.SET_CURRENT_PAGE(page)
    },
    
    onItemsPerPageChange(count) {
      this.SET_ITEMS_PER_PAGE(count)
      this.SET_CURRENT_PAGE(1) // Nulstil til første side ved ændring af antal per side
    },
    
    clearError() {
      this.CLEAR_ERROR()
    },
    
    viewMeterDetails(meter) {
      this.$router.push({ name: 'MeterDetail', params: { mac: meter.mac } })
    }
  },
  async created() {
    // Indlæs målere ved komponentens oprettelse
    if (this.meters.length === 0) {
      await this.fetchMeters()
    }
  }
}
</script>

<style scoped>
.meter-overview {
  padding: 1rem 0;
}

.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.search-box {
  display: flex;
  flex: 1;
  max-width: 500px;
}

.search-box input {
  flex: 1;
  margin-right: 0.5rem;
}

.filter-toggle {
  display: flex;
  align-items: center;
}

.filter-toggle label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.filter-toggle input {
  margin-right: 0.5rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-top: 2rem;
}

.empty-state h3 {
  margin-bottom: 1rem;
  color: #6c757d;
}

.empty-state p {
  color: #6c757d;
  margin-bottom: 1.5rem;
}

.meter-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-box {
  flex: 1;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stat-box h3 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 600;
  color: #212529;
}

.stat-box p {
  margin: 0.5rem 0 0;
  color: #6c757d;
  font-size: 0.9rem;
}

.stat-box.active h3 {
  color: #28a745;
}

.stat-box.inactive h3 {
  color: #dc3545;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 768px) {
  .actions-bar {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .search-box {
    max-width: 100%;
    width: 100%;
    margin-bottom: 1rem;
  }
  
  .meter-stats {
    flex-direction: column;
  }
  
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
