const express = require("express");
const path = require("path");
const { createProxyMiddleware } = require("http-proxy-middleware");

const app = express();
const port = process.env.PORT || 8080;

// Setup static resources using dist (created by `npm run build`)
app.use(express.static(path.join(__dirname, "dist")));

// Define the proxy path for the azure functions
const azureFunctionProxy = createProxyMiddleware("/api", {
  target: process.env.BACKEND_URL || "http://localhost:8000",
  changeOrigin: true,
  pathRewrite: {
    "^/api": "", 
  }
});
app.use(azureFunctionProxy);

// Define index get
app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "dist", "index.html"));
});

// Begin listening
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
  console.log(process.env.BACKEND_URL || "http://localhost:8000");
});
