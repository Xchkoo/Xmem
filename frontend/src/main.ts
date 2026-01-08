import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./assets/tailwind.css";
import { vSecureDisplay } from "./directives/secureDisplay";

const app = createApp(App);
app.use(createPinia());
app.use(router).directive("secure-display", vSecureDisplay).mount("#app");

