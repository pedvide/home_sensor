import axios from "axios";

function fetchData(name, limit = 5) {
  const baseURI = `http://home-sensor.home/api/${name}?limit=${limit}`;
  axios
    .get(baseURI)
    .then((result) => {
      this[name] = result.data;
    })
    .catch((error) => console.log(error));
}

function checkHealth(hostname) {
  const baseURI = `http://${hostname}/health`;
  axios
    .get(baseURI)
    .then((result) => {
      this.health = result.data === "Ok" || result.data.status === "Ok";
    })
    .catch(() => {
      this.health = false;
    });
}

export { fetchData, checkHealth };
