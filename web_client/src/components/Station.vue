<template>
  <div class="card">
    <div class="content">
      <h4>Station {{ station.id }}</h4>
      <p>Located at {{ station.location }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: "Station",
  props: {
    station: {
      default: () => "",
      type: Object,
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
@import "../assets/card.css";
</style>
