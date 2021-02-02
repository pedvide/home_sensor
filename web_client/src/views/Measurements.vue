<template>
  <article class="measurements">
    <ol id="measurement">
      <li
        v-for="m in measurements"
        :key="`${m.timestamp}-${m.station_id}-${m.sensor_id}-${m.magnitude.id}`"
      >
        <Measurement :m="m" />
      </li>
    </ol>
  </article>
</template>

<script>
import fetchData from "@/utils/api_query";
import Measurement from "@/components/Measurement.vue";

export default {
  name: "Measurements",
  components: { Measurement },
  data() {
    return {
      measurements: [],
      refreshTimer: null,
    };
  },

  created() {
    fetchData.call(this, "measurements", 10);
    this.refreshTimer = setInterval(
      fetchData.bind(this),
      500,
      "measurements",
      10
    );
  },

  beforeRouteLeave(to, from, next) {
    clearInterval(this.refreshTimer);
    next();
  },

  methods: {},
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
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
