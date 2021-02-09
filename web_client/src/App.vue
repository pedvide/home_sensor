<template>
  <div id="app">
    <header>
      <h1>Home Sensor</h1>
      <nav>
        <router-link to="/">Stations</router-link> |
        <router-link to="/sensors">Sensors</router-link> |
        <router-link to="/measurements">Measurements</router-link> |
        <a
          href="http://home-sensor.home/grafana/d/h45MReWRk/home-sensor?orgId=1&refresh=5m"
          target="_blank"
        >
          Dashboard
        </a>
      </nav>
    </header>
    <router-view />
  </div>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

body {
  margin: auto;
}
/* Desktop Styles */
@media only screen and (max-width: 961px) {
  body {
    width: 100%;
  }
}
/* app Styles */
@media only screen and (min-width: 961px) {
  body {
    width: 960px;
  }
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
}

a[href^="http://"]
{
  background: url("~@/assets/external-link.png") center right no-repeat;
  padding-right: 13px;
}
</style>
