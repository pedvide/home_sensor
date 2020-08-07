<template>
  <article class="measurements-feed">
    <h1>Live Measurements Feed</h1>
    <ol id="measurement-feed">
      <li v-for="m in measurements" :key="m.id">
        <Measurement :m="m" />
      </li>
    </ol>
  </article>
</template>

<script>
import axios from "axios";
import Measurement from "@/components/Measurement.vue";

export default {
  name: "MeasurementsFeed",
  components: { Measurement },
  data() {
    return {
      measurements: [],
    };
  },
  created() {
    this.fetchMeasurements();
    setInterval(this.fetchMeasurements, 1000);
  },
  watch: {
    // call again the method if the route changes
    $route: "fetchData",
  },
  methods: {
    fetchMeasurements() {
      const baseURI = "http://home-sensor.home/api/measurements";
      axios
        .get(baseURI)
        .then((result) => {
          this.measurements = result.data;
        })
        .catch((error) => console.log(error));
    },
  },
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
