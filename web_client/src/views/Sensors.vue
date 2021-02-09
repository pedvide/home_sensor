<template>
  <article class="sensors">
    <ol id="sensors-list" class="list">
      <li v-for="s in sensors" :key="s.id" class="list">
        <Sensor :sensor="s" />
      </li>
    </ol>
  </article>
</template>

<script>
// @ is an alias to /src
import { fetchData } from "@/utils/api_query";
import Sensor from "@/components/Sensor.vue";

export default {
  name: "Sensors",
  components: {
    Sensor,
  },
  data() {
    return {
      sensors: [],
    };
  },
  created() {
    fetchData.call(this, "sensors", 20);
  },
  watch: {
    $route() {
      fetchData.call(this, "sensors", 20);
    },
  },
};
</script>

<style scoped>
@import "../assets/card.css";
</style>
