import { defineStore } from "pinia";

export const useUiStore = defineStore("ui", {
  state: () => ({
    routeLoadingCount: 0,
  }),
  getters: {
    routeLoading: (state) => state.routeLoadingCount > 0,
  },
  actions: {
    startRouteLoading() {
      this.routeLoadingCount += 1;
    },
    stopRouteLoading() {
      this.routeLoadingCount = Math.max(0, this.routeLoadingCount - 1);
    },
    resetRouteLoading() {
      this.routeLoadingCount = 0;
    },
  },
});

