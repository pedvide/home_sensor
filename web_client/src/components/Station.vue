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
.card {
  /* Add shadows to create the "card" effect */
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
  transition: 0.3s;
}

/* On mouse-over, add a deeper shadow */
.card:hover {
  box-shadow: 0 8px 16px 0 rgba(0, 0, 0, 0.2);
}

/* Add some padding inside the card content */
.content {
  padding: 2px 16px;
}
</style>
