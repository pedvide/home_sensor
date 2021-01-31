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
@import "../assets/card.css";
</style>
