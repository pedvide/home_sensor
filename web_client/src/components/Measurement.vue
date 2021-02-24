<template>
  <div class="card">
    <div class="content">
      <h5>
        {{
          new Date(m.timestamp * 1000)
            .toString()
            .split("(")[0]
            .split("GMT")[0]
            .trim()
        }}
      </h5>
      <p>
        {{ m.magnitude.name[0].toUpperCase() + m.magnitude.name.substring(1) }}
        {{ formatMagnitude(m.value, m.magnitude.precision) }}
        {{ m.magnitude.unit === "C" ? "°C" : m.magnitude.unit }}
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
  methods: {
    formatMagnitude(value, precision) {
      const orderOfMagnitude = Math.floor(Math.log10(precision));
      if (orderOfMagnitude < 0) {
        return parseFloat(value).toFixed(-orderOfMagnitude);
      }
      return parseFloat(
        parseInt(value, 10).toPrecision(value.length - orderOfMagnitude)
      );
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
@import "../assets/card.css";
</style>
