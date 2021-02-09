import Vue from "vue";
import VueRouter from "vue-router";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "Stations",
    component: () => import("../views/Stations.vue"),
  },
  {
    path: "/sensors",
    name: "Sensors",
    component: () => import("../views/Sensors.vue"),
  },
  {
    path: "/measurements",
    name: "Measurements",
    component: () => import("../views/Measurements.vue"),
  },
  {
    path: "*",
    name: "404",
    component: () => import(/* webpackChunkName: "404" */ "../views/404.vue"),
  },
];

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes,
});

export default router;
