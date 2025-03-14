<template>
  <div id="app">
    <header>
      <nav>
        <router-link to="/">Måler Oversigt</router-link> |
        <router-link to="/scan">Søg Efter Nye Målere</router-link>
      </nav>
      <h1>Måler Overvågningssystem</h1>
    </header>
    
    <main>
      <router-view/>
    </main>
    
    <footer>
      <p>Måler Overvågningssystem &copy; {{ currentYear }} Jelling Camping</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    currentYear() {
      return new Date().getFullYear();
    }
  }
}
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Roboto', sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f4f4f4;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

header {
  background-color: #0056b3;
  color: #fff;
  padding: 1rem;
  text-align: center;
}

header h1 {
  margin: 0.5rem 0;
}

nav {
  padding: 0.5rem 0;
}

nav a {
  color: #fff;
  margin: 0 0.5rem;
  text-decoration: none;
  font-weight: 500;
}

nav a.router-link-exact-active {
  font-weight: bold;
  text-decoration: underline;
}

main {
  flex: 1;
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

footer {
  background-color: #333;
  color: #fff;
  text-align: center;
  padding: 1rem;
  margin-top: auto;
}

.container {
  padding: 1rem;
  background-color: #fff;
  border-radius: 5px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  background-color: #0056b3;
  color: #fff;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.btn:hover {
  background-color: #003d7a;
}

.btn-danger {
  background-color: #dc3545;
}

.btn-danger:hover {
  background-color: #a71d2a;
}

.btn-success {
  background-color: #28a745;
}

.btn-success:hover {
  background-color: #1c7430;
}

.form-group {
  margin-bottom: 1rem;
}

.form-control {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.alert {
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
  border-radius: 0.25rem;
}

.alert-danger {
  color: #721c24;
  background-color: #f8d7da;
  border-color: #f5c6cb;
}

.alert-success {
  color: #155724;
  background-color: #d4edda;
  border-color: #c3e6cb;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
