// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "integritas-mcp-server",
      cwd: "/home/integritas-mcp-server",
      // Use the console script from your virtualenv (absolute path is safest)
      script: "/root/.local/bin/uv",
      args: "run integritas-mcp http --host 127.0.0.1 --port 8787",

      // Tell PM2 this is a binary, not Node.js
      interpreter: "none",
      exec_mode: "fork",

      // Logging
      out_file: "/var/log/integritas-mcp/out.log",
      error_file: "/var/log/integritas-mcp/err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",

      // Stability
      autorestart: true,
      max_restarts: 10,
      min_uptime: "5s",

      time: true,
      watch: false,
    },
  ],
};
