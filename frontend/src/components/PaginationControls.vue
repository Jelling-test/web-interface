<template>
  <div class="pagination-container" v-if="totalPages > 1">
    <div class="pagination-controls">
      <button 
        class="page-button prev" 
        @click="onPageChange(currentPage - 1)" 
        :disabled="currentPage === 1"
        aria-label="Forrige side"
      >
        <span class="page-arrow">&#9664;</span>
      </button>
      
      <div class="page-numbers">
        <!-- Første side knap -->
        <button 
          v-if="showFirst" 
          class="page-button" 
          :class="{ active: currentPage === 1 }"
          @click="onPageChange(1)"
        >
          1
        </button>
        
        <!-- Ellipse hvis nødvendig -->
        <span v-if="showFirstEllipsis" class="ellipsis">...</span>
        
        <!-- Midterste sider -->
        <button 
          v-for="page in visiblePageNumbers" 
          :key="page" 
          class="page-button" 
          :class="{ active: currentPage === page }"
          @click="onPageChange(page)"
        >
          {{ page }}
        </button>
        
        <!-- Ellipse hvis nødvendig -->
        <span v-if="showLastEllipsis" class="ellipsis">...</span>
        
        <!-- Sidste side knap -->
        <button 
          v-if="showLast" 
          class="page-button" 
          :class="{ active: currentPage === totalPages }"
          @click="onPageChange(totalPages)"
        >
          {{ totalPages }}
        </button>
      </div>
      
      <button 
        class="page-button next" 
        @click="onPageChange(currentPage + 1)" 
        :disabled="currentPage === totalPages"
        aria-label="Næste side"
      >
        <span class="page-arrow">&#9654;</span>
      </button>
    </div>
    
    <div class="pagination-info">
      <span>Side {{ currentPage }} af {{ totalPages }}</span>
      
      <div class="items-per-page" v-if="showItemsPerPage">
        <label for="itemsPerPage">Vis:</label>
        <select 
          id="itemsPerPage" 
          v-model="selectedItemsPerPage"
          @change="onItemsPerPageChange"
        >
          <option 
            v-for="option in itemsPerPageOptions" 
            :key="option" 
            :value="option"
          >
            {{ option }}
          </option>
        </select>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PaginationControls',
  props: {
    currentPage: {
      type: Number,
      required: true
    },
    totalPages: {
      type: Number,
      required: true
    },
    maxVisiblePages: {
      type: Number,
      default: 5
    },
    itemsPerPage: {
      type: Number,
      default: 12
    },
    itemsPerPageOptions: {
      type: Array,
      default: () => [6, 12, 24, 48]
    },
    showItemsPerPage: {
      type: Boolean,
      default: true
    }
  },
  emits: ['page-change', 'items-per-page-change'],
  data() {
    return {
      selectedItemsPerPage: this.itemsPerPage
    }
  },
  computed: {
    // Beregn hvilke sidenumre der skal vises baseret på nuværende side og totale sider
    visiblePageNumbers() {
      if (this.totalPages <= this.maxVisiblePages) {
        // Hvis der er færre sider end maxVisiblePages, vis alle sider
        return Array.from({ length: this.totalPages }, (_, i) => i + 1).filter(page => 
          page !== 1 && page !== this.totalPages
        )
      }
      
      // Bestem startside
      let start = Math.max(
        2,
        this.currentPage - Math.floor((this.maxVisiblePages - 2) / 2)
      )
      
      // Bestem slutside
      let end = Math.min(
        this.totalPages - 1,
        start + this.maxVisiblePages - 3
      )
      
      // Juster start hvis end er tæt på totalPages
      if (end >= this.totalPages - 1) {
        start = Math.max(2, this.totalPages - this.maxVisiblePages + 1)
      }
      
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },
    // Om første side skal vises separat
    showFirst() {
      return this.totalPages > 1
    },
    // Om sidste side skal vises separat
    showLast() {
      return this.totalPages > 1 && this.totalPages !== 1
    },
    // Om ellipsis skal vises før midterste sidenumre
    showFirstEllipsis() {
      return this.totalPages > this.maxVisiblePages && this.visiblePageNumbers[0] > 2
    },
    // Om ellipsis skal vises efter midterste sidenumre
    showLastEllipsis() {
      return this.totalPages > this.maxVisiblePages && 
        this.visiblePageNumbers[this.visiblePageNumbers.length - 1] < this.totalPages - 1
    }
  },
  methods: {
    onPageChange(page) {
      if (page >= 1 && page <= this.totalPages && page !== this.currentPage) {
        this.$emit('page-change', page)
      }
    },
    onItemsPerPageChange() {
      this.$emit('items-per-page-change', this.selectedItemsPerPage)
    }
  },
  watch: {
    // Opdater det valgte itemsPerPage hvis prop ændres
    itemsPerPage(newValue) {
      this.selectedItemsPerPage = newValue
    }
  }
}
</script>

<style scoped>
.pagination-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 1.5rem 0;
  gap: 0.75rem;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.page-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 0.5rem;
  background-color: #fff;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  color: #495057;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.page-button:hover:not(:disabled) {
  background-color: #f8f9fa;
  border-color: #adb5bd;
  color: #212529;
}

.page-button.active {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
  font-weight: 500;
}

.page-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-button.prev, .page-button.next {
  padding: 0;
  width: 2rem;
}

.page-arrow {
  font-size: 0.75rem;
}

.page-numbers {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.ellipsis {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  color: #6c757d;
}

.pagination-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  font-size: 0.9rem;
  color: #6c757d;
}

.items-per-page {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.items-per-page select {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background-color: #fff;
  font-size: 0.9rem;
}

@media (min-width: 768px) {
  .pagination-container {
    flex-direction: row;
    justify-content: space-between;
  }
}
</style>
