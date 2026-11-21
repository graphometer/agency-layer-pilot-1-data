const http = require("http");

const server = http.createServer((req, res) => {
  if (req.method === "POST" && req.url === "/users") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ id: 1, name: "stub" }));
    return;
  }
  res.writeHead(404);
  res.end();
});

module.exports = server;
