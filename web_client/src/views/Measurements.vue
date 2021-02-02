<template>
  <article class="measurements">
    <transition-group name="list" tag="ol">
      <li
        v-for="m in measurements"
        :key="`${m.timestamp}-${m.station_id}-${m.sensor_id}-${m.magnitude.id}`"
        class="list-item"
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
      500,
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
ol {
  list-style-type: none;
  display: inline-block;
  text-align: left;
}

.list-complete-item {
  transition: all 0.5s;
  display: inline-block;
  margin-right: 10px;
}
.list-enter-active,
.list-leave-active {
  transition: all 0.5s;
}
.list-enter, .list-leave-to /* .list-leave-active below version 2.1.8 */ {
  opacity: 0;
  /* transform: translateX(30px); */
}
.list-move {
  transition: transform 0.5s;
}
</style>
