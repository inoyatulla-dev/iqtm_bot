import React from "react";
import ReactDOM from "react-dom/client";
import { AppRoot } from "@telegram-apps/telegram-ui";
import "@telegram-apps/telegram-ui/dist/styles.css";
import "./index.css";

import { initTelegram } from "./telegram";
import { AuthProvider } from "./store/auth";
import { App } from "./App";

initTelegram();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppRoot appearance="dark">
      <AuthProvider>
        <App />
      </AuthProvider>
    </AppRoot>
  </React.StrictMode>
);
