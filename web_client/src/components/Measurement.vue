<template>
  <div class="measurement">
    Station #{{ m.station_id }}
    {{ Date(m.timestamp).toLocaleString().split("(")[0].trim() }}
    {{ m.magnitude.name[0].toUpperCase() + m.magnitude.name.substring(1) }}
    {{ parseFloat(m.value).toFixed(-Math.log10(m.magnitude.precision)) }} {{ m.magnitude.unit }}
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
ol {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
</style>
