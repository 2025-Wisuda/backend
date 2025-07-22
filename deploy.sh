#!/bin/bash
# Deploy backend using docker-compose (to be run on VPS)
# Usage: ./deploy.sh

set -e

PROJECT_DIR="/opt/backend"
COMPOSE_FILE="docker-compose.yml"

cd "$PROJECT_DIR"

# Stop and remove existing containers
sudo docker-compose -f "$COMPOSE_FILE" down

# Build and start containers in detached mode
sudo docker-compose -f "$COMPOSE_FILE" up -d --build

# Show status
sudo docker-compose -f "$COMPOSE_FILE" ps

if [ $? -eq 0 ]; then
  echo "\n✅ Backend successfully deployed and running via docker-compose."
else
  echo "\n❌ Deployment failed. Please check docker-compose logs."
fi 