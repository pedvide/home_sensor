import axios from "axios";

function fetchData(name) {
  const baseURI = `http://home-sensor.home/api/${name}`;
  axios
    .get(baseURI)
    .then((result) => {
      this[name] = result.data;
    })
    .catch((error) => console.log(error));
}

export default fetchData;
