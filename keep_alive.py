# UptimeRobot health check is handled by the webhook server itself.
# PTB's run_webhook serves on PORT and responds to all paths.
# Point UptimeRobot to: https://your-render-url.onrender.com/
# It will get a 200 OK from the webhook server.

def keep_alive():
    pass  # No-op — PTB webhook server keeps the process alive
