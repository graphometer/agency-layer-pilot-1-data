// Build step for the kiosk page: copies src/index.html to dist/index.html.
const fs = require("fs");

fs.mkdirSync("dist", { recursive: true });
fs.copyFileSync("src/index.html", "dist/index.html");
console.log("built dist/index.html");
