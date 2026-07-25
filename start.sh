#!/bin/bash
# Render sets the $PORT environment variable.
# We substitute the placeholder port 8080 in nginx.conf with the actual port Render gives us.
sed -i "s/listen 8080;/listen ${PORT:-8080};/g" /etc/nginx/nginx.conf

# Start supervisord to launch Nginx, FastAPI, and Streamlit
exec /usr/local/bin/supervisord -c /app/supervisord.conf
