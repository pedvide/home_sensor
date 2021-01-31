<template>
  <div class="card">
    <div class="content">
      <h4>{{ sensor.name }}</h4>
      <ol id="magnitudes-list">
        <li v-for="mag in sensor.magnitudes" :key="mag.id">
          <div class="card">
            <div class="content">
              <p>{{ mag.name }} ({{ mag.unit }})</p>
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
      default: () => "",
      type: Object,
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
@import "../assets/card.css";
ol {
  list-style-type: none;
  display: inline-block;
  text-align: left;
}
</style>
