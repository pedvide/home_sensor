import { createRouter, createWebHistory } from "vue-router";

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
    path: "/:pathMatch(.*)*",
    name: "404",
    component: () => import(/* webpackChunkName: "404" */ "../views/404.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
