<template>
  <div class="card">
    <div class="content">
      <h4>
        Name:
        {{ m.magnitude.name[0].toUpperCase() + m.magnitude.name.substring(1) }}
      </h4>
      <p>Date: {{ Date(m.timestamp).toLocaleString().split("(")[0].trim() }}</p>
      <p>
        Value:
        {{ parseFloat(m.value).toFixed(-Math.log10(m.magnitude.precision)) }}
        {{ m.magnitude.unit }}
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: "Measurement",
  props: {
    m: {
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
