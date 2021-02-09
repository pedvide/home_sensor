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
    };
  },
  created() {
    fetchData.call(this, "stations", 20);
  },
  watch: {
    $route() {
      fetchData.call(this, "stations", 20);
    },
  },
};
</script>

<style scoped>
@import "../assets/card.css";
</style>
