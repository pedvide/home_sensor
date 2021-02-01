<template>
  <article class="stations">
    <ol id="stations-list">
      <li v-for="s in stations" :key="s.id">
        <Station :station="s" />
      </li>
    </ol>
  </article>
</template>

<script>
// @ is an alias to /src
import fetchData from "@/utils/api_query";
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
    fetchData.call(this, "stations");
    this.refreshTimer = setInterval(fetchData.bind(this), 1000, "stations");
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.refreshTimer);
    next();
  },
};
</script>

<style scoped>
ol {
  list-style-type: none;
  display: inline-block;
  text-align: left;
}
/* li {
  display: inline-block;
  margin: 0 10px;
} */
</style>
