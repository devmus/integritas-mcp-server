module.exports = {
  apps: [
    {
      name: "integritas-mcp-server",
      cwd: "/home/integritas-mcp-server",
      script: "/bin/bash",
      args: ["-lc", "uv run integritas-mcp sse --host 127.0.0.1 --port 8787"],

      // This is a native binary, not Node
      interpreter: "none",
      exec_mode: "fork",

      out_file: "/var/log/integritas-mcp/out.log",
      error_file: "/var/log/integritas-mcp/err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      autorestart: true,
      min_uptime: "5s",
      max_restarts: 10,
      time: true,
      watch: false,
      restart_delay: 3000,
    },
  ],
};
