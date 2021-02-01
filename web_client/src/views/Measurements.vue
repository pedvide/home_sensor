<template>
  <article class="measurements">
    <ol id="measurement">
      <li v-for="m in measurements" :key="m.id">
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
    };
  },
  created() {
    fetchData.call(this, "measurements");
    setInterval(fetchData.bind(this), 1000, "measurements");
  },
  watch: {
    // call again the method if the route changes
    // $route: "fetchData",
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
