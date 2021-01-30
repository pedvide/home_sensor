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
    };
  },
  created() {
    fetchData.call(this, "stations");
    setInterval(fetchData.bind(this), 1000, "stations");
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
