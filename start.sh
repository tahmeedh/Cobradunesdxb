#!/bin/bash
# Start API server in background
node server.js &
API_PID=$!

# Start Astro dev server
npx astro dev --host 0.0.0.0 --port 5000

# When astro exits, kill API server
kill $API_PID 2>/dev/null
