#!/bin/sh
set -e

# Set default value if not provided
export VITE_API_BASE_URL=${VITE_API_BASE_URL:-""}

# Use envsubst to replace environment variables in index.html template
envsubst '${VITE_API_BASE_URL}' < /usr/share/nginx/html/index.html.template > /usr/share/nginx/html/index.html

# Execute the original nginx entrypoint
exec "$@"

