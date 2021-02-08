<template>
  <article class="stations">
    <ol id="stations-list" class="list">
      <li v-for="s in stations" :key="s.id" class="list">
        <Station :station="s" />
      </li>
    </ol>
  </article>
</template>

<script>
// @ is an alias to /src
import { fetchData } from "@/utils/api_query";
import Station from "@/components/Station.vue";

export default {
  name: "Stations",
  components: {
    Station,
  },
  data() {
    return {
      stations: [],
      refreshTimer: null,
    };
  },
  created() {
    fetchData.call(this, "stations", 20);
    this.refreshTimer = setInterval(fetchData.bind(this), 1000, "stations", 20);
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.refreshTimer);
    next();
  },
};
</script>

<style scoped>
@import "../assets/card.css";
</style>
