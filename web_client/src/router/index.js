import Vue from "vue";
import VueRouter from "vue-router";
import Stations from "../views/Stations.vue";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "Stations",
    component: Stations,
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
    path: "/about",
    name: "About",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ "../views/About.vue"),
  },
];

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes,
});

export default router;
