import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./assets/tailwind.css";
import { vSecureDisplay } from "./directives/secureDisplay";

const app = createApp(App);
/**
 * 捕获未处理的运行时错误，并引导到 500 页面以便用户恢复。
 */
app.config.errorHandler = () => {
  router.replace({ name: "server-error" });
};
app.use(createPinia());
app.use(router).directive("secure-display", vSecureDisplay).mount("#app");

