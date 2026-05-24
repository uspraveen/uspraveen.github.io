#!/bin/bash
cd /tmp/site
fuser -k 3001/tcp 2>/dev/null || true
nohup node api/server.js > /tmp/api.log 2>&1 &
echo "API started on port 3001"
