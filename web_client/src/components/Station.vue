<template>
  <div @click="showSensors = !showSensors" class="card">
    <div class="content">
      <h4>
        <span :class="`station-status ${health ? 'active' : 'inactive'}`">
          ●
        </span>
        Station {{ station.id }}
        <a
          @click.stop
          :href="'http://' + station.hostname + '.home'"
          target="_blank"
          style="float: right"
        >
          Logs
        </a>
      </h4>
      <p>Located at the {{ station.location }}</p>
      <transition name="sensors">
        <ol v-if="showSensors" @click.stop class="list">
          <li v-for="s in station.sensors" :key="s.id" class="list">
            <Sensor :sensor="s" />
          </li>
        </ol>
      </transition>
    </div>
  </div>
</template>

<script>
import { checkHealth } from "@/utils/api_query";
import Sensor from "@/components/Sensor.vue";

export default {
  name: "Station",
  components: {
    Sensor,
  },
  props: {
    station: {
      default: () => {},
      type: Object,
    },
    checkHealthInterval: {
      default: () => 5000,
      type: Number,
    },
  },
  data() {
    return {
      showSensors: false,
      health: true,
    };
  },
  created() {
    checkHealth.call(this, this.station.hostname);
    this.checkHealthTimer = setInterval(
      checkHealth.bind(this),
      this.checkHealthInterval,
      this.station.hostname
    );
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.checkHealthTimer);
    next();
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
@import "../assets/card.css";

.list .list {
  width: 100%;
}

.sensors-enter-active,
.sensors-leave-active {
  transition: opacity 0.15s;
}
.sensors-enter,
.sensors-leave-to {
  opacity: 0;
}

.station-status {
  position: relative;
  top: -0.1em;
}
.station-status.active {
  color: green;
}
.station-status.inactive {
  color: red;
}
</style>
