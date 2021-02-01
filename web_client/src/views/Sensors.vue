<template>
  <article class="sensors">
    <ol id="sensors-list">
      <li v-for="s in sensors" :key="s.id">
        <Sensor :sensor="s" />
      </li>
    </ol>
  </article>
</template>

<script>
// @ is an alias to /src
import fetchData from "@/utils/api_query";
import Sensor from "@/components/Sensor.vue";

export default {
  name: "Sensors",
  components: {
    Sensor,
  },
  data() {
    return {
      sensors: [],
      refreshTimer: null,
    };
  },
  created() {
    fetchData.call(this, "sensors");
    this.refreshTimer = setInterval(fetchData.bind(this), 1000, "sensors");
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
