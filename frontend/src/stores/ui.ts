import { defineStore } from "pinia";

export const useUiStore = defineStore("ui", {
  state: () => ({
    routeState: "idle" as "idle" | "bar" | "loading",
    routeNavToken: 0,
    routeStartedAt: null as number | null,
    routeLoadingShownAt: null as number | null,
    routeShowBarAfterMs: 80,
    routeShowLoadingAfterMs: 250,
    routeMinBarMs: 200,
    routeMinLoadingMs: 500,
    routeShowBarTimer: null as number | null,
    routeShowLoadingTimer: null as number | null,
    routeStopTimer: null as number | null,
  }),
  getters: {
    routeBar: (state) => state.routeState === "bar",
    routeLoading: (state) => state.routeState === "loading",
  },
  actions: {
    setRouteMinLoadingMs(ms: number) {
      const value = Number.isFinite(ms) ? Math.max(0, Math.floor(ms)) : 0;
      this.routeMinLoadingMs = value;
    },
    startRouteTransition() {
      this.routeNavToken += 1;
      const token = this.routeNavToken;

      if (this.routeShowBarTimer !== null) {
        window.clearTimeout(this.routeShowBarTimer);
        this.routeShowBarTimer = null;
      }
      if (this.routeShowLoadingTimer !== null) {
        window.clearTimeout(this.routeShowLoadingTimer);
        this.routeShowLoadingTimer = null;
      }
      if (this.routeStopTimer !== null) {
        window.clearTimeout(this.routeStopTimer);
        this.routeStopTimer = null;
      }

      this.routeStartedAt = Date.now();
      this.routeLoadingShownAt = null;
      this.routeState = "idle";

      this.routeShowBarTimer = window.setTimeout(() => {
        if (this.routeNavToken !== token) return;
        if (this.routeState !== "idle") return;
        this.routeState = "bar";
        this.routeShowBarTimer = null;
      }, this.routeShowBarAfterMs);

      this.routeShowLoadingTimer = window.setTimeout(() => {
        if (this.routeNavToken !== token) return;
        if (this.routeState !== "idle" && this.routeState !== "bar") return;
        this.routeState = "loading";
        this.routeLoadingShownAt = Date.now();
        this.routeShowLoadingTimer = null;
      }, this.routeShowLoadingAfterMs);
    },
    finishRouteTransition() {
      const token = this.routeNavToken;

      if (this.routeShowBarTimer !== null) {
        window.clearTimeout(this.routeShowBarTimer);
        this.routeShowBarTimer = null;
      }
      if (this.routeShowLoadingTimer !== null) {
        window.clearTimeout(this.routeShowLoadingTimer);
        this.routeShowLoadingTimer = null;
      }
      if (this.routeStopTimer !== null) {
        window.clearTimeout(this.routeStopTimer);
        this.routeStopTimer = null;
      }

      const now = Date.now();

      if (this.routeState === "loading") {
        const shownAt = this.routeLoadingShownAt ?? now;
        const elapsed = now - shownAt;
        const remaining = this.routeMinLoadingMs - elapsed;

        if (remaining > 0) {
          this.routeStopTimer = window.setTimeout(() => {
            if (this.routeNavToken !== token) return;
            this.routeState = "idle";
            this.routeStartedAt = null;
            this.routeLoadingShownAt = null;
            this.routeStopTimer = null;
          }, remaining);
          return;
        }

        this.routeState = "idle";
        this.routeStartedAt = null;
        this.routeLoadingShownAt = null;
        return;
      }

      if (this.routeState === "bar") {
        const startedAt = this.routeStartedAt ?? now;
        const elapsed = now - startedAt;
        const remaining = this.routeMinBarMs - elapsed;

        if (remaining > 0) {
          this.routeStopTimer = window.setTimeout(() => {
            if (this.routeNavToken !== token) return;
            this.routeState = "idle";
            this.routeStartedAt = null;
            this.routeStopTimer = null;
          }, remaining);
          return;
        }

        this.routeState = "idle";
        this.routeStartedAt = null;
        return;
      }
    },
    resetRouteTransition() {
      if (this.routeShowBarTimer !== null) {
        window.clearTimeout(this.routeShowBarTimer);
        this.routeShowBarTimer = null;
      }
      if (this.routeShowLoadingTimer !== null) {
        window.clearTimeout(this.routeShowLoadingTimer);
        this.routeShowLoadingTimer = null;
      }
      if (this.routeStopTimer !== null) {
        window.clearTimeout(this.routeStopTimer);
        this.routeStopTimer = null;
      }

      this.routeState = "idle";
      this.routeStartedAt = null;
      this.routeLoadingShownAt = null;
    },
  },
});

