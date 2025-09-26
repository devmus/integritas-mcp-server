module.exports = {
  apps: [
    {
      name: "integritas-mcp-server",
      cwd: "/home/integritas-mcp-server",
      script: "/home/integritas/.local/bin/uv", // << use `which uv` to confirm
      args: [
        "run",
        "integritas-mcp",
        "sse",
        "--host",
        "127.0.0.1",
        "--port",
        "8787",
      ],
      interpreter: "none",
      exec_mode: "fork",

      out_file: "/var/log/integritas-mcp/out.log",
      error_file: "/var/log/integritas-mcp/err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      autorestart: true,
      min_uptime: "5s",
      max_restarts: 10,
      time: true,
    },
  ],
};
