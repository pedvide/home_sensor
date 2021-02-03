<template>
  <article class="measurements">
    <transition-group name="dynamic-list" tag="ol" class="list">
      <li
        v-for="m in measurements"
        :key="`${m.timestamp}-${m.station_id}-${m.sensor_id}-${m.magnitude.id}`"
        class="list"
      >
        <Measurement :m="m" />
      </li>
    </transition-group>
  </article>
</template>

<script>
import fetchData from "@/utils/api_query";
import Measurement from "@/components/Measurement.vue";

export default {
  name: "Measurements",
  components: { Measurement },
  data() {
    return {
      measurements: [],
      refreshTimer: null,
    };
  },

  created() {
    fetchData.call(this, "measurements", 10);
    this.refreshTimer = setInterval(
      fetchData.bind(this),
      750,
      "measurements",
      10
    );
  },

  beforeRouteLeave(to, from, next) {
    clearInterval(this.refreshTimer);
    next();
  },

  methods: {},
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
@import "../assets/card.css";
ol.list {
  flex-direction: column;
  align-items: center;
}
.card {
  min-height: 0px;
}

.dynamic-list-enter-active,
.dynamic-list-leave-active {
  transition: all 0.75s;
}
.dynamic-list-enter,
.dynamic-list-leave-to {
  opacity: 0;
}
.dynamic-list-move {
  transition: transform 0.75s;
}
</style>
