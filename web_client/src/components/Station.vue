<template>
  <div @click="showSensors = !showSensors" class="card">
    <div class="content">
      <h4>Station {{ station.id }}</h4>
      <p>Located at the {{ station.location }}</p>
      <ol v-if="showSensors" class="list">
        <li v-for="s in station.sensors" :key="s.id" class="list">
          <Sensor :sensor="s" />
        </li>
      </ol>
    </div>
  </div>
</template>

<script>
import Sensor from "@/components/Sensor.vue";

export default {
  name: "Station",
  components: {
    Sensor,
  },
  props: {
    station: {
      default: () => "",
      type: Object,
    },
  },
  data() {
    return {
      showSensors: false,
    };
  },
  methods: {
    testFunction(event) {
      console.log("test clicked");
      console.log(event);
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
@import "../assets/card.css";
</style>
