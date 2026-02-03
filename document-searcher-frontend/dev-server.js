const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

const app = express();

// Make sure our own 3100 responses are safe (fallback)
app.use((req, res, next) => {
  res.setHeader("Cross-Origin-Opener-Policy", "unsafe-none");
  res.setHeader("Cross-Origin-Embedder-Policy", "unsafe-none");
  next();
});

// Proxy EVERYTHING to CRA on :3000 and override CRA response headers
app.use(
  "/",
  createProxyMiddleware({
    target: "http://localhost:3000",
    changeOrigin: true,
    ws: true,
    onProxyRes: (proxyRes /*, req, res*/) => {
      // Force headers on the response coming back from CRA
      proxyRes.headers["cross-origin-opener-policy"] = "unsafe-none";
      proxyRes.headers["cross-origin-embedder-policy"] = "unsafe-none";
      // (Optional) If you set a strict CSP elsewhere and want to relax for dev, you could modify here too.
    },
  })
);

const PORT = 3100;
app.listen(PORT, () =>
  console.log(`Header wrapper running at http://localhost:${PORT}`)
);