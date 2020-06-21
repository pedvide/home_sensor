<template>
  <article class="measurements-feed">
    <h1>Live Measurements Feed</h1>
  </article>
</template>

<script>
import axios from "axios";

export default {
  name: "MeasurementsFeed",
  components: {},
  data() {
    return {
      users: [],
    };
  },
  methods: {
    fetchMeasurements() {
      const baseURI = "https://jsonplaceholder.typicode.com/users";
      axios
        .get(baseURI)
        .then((result) => {
          this.users = result.data;
        })
        .catch((error) => console.log(error));
    },
  },
};
</script>
