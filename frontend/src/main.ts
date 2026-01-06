import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import "./assets/tailwind.css";
import { vSecureDisplay } from "./directives/secureDisplay";

const app = createApp(App);
app.use(createPinia());
app.directive("secure-display", vSecureDisplay);
app.mount("#app");

