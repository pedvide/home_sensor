<template>
  <div
    @click="showMagnitudes = !showMagnitudes"
    :style="showMagnitudes ? '' : 'min-height: unset;'"
    class="card"
  >
    <div class="content">
      <h4>
        {{ sensor.name }} <span v-if="sensor.tag">({{ sensor.tag }})</span>
      </h4>
      <ol v-if="showMagnitudes" id="magnitudes-list" class="list">
        <li v-for="mag in sensor.magnitudes" :key="mag.id" class="list">
          <div class="card">
            <div class="content">
              <h5>{{ mag.name }} ({{ mag.unit }})</h5>
            </div>
          </div>
        </li>
      </ol>
    </div>
  </div>
</template>

<script>
export default {
  name: "Sensor",
  props: {
    sensor: {
      default: () => {},
      type: Object,
    },
  },
  data() {
    return {
      showMagnitudes: true,
    };
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
@import "../assets/card.css";
/* Reset some settings for nested cards and lists */
.card .card {
  width: auto;
  min-height: auto;
}
@media only screen and (max-width: 961px) {
  ol.list ol.list {
    flex-direction: row;
    justify-content: left;
  }
}
</style>
