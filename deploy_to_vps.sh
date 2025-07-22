#!/bin/bash
# Deploy backend to VPS using rsync with exclusions
# Usage: ./deploy_to_vps.sh

VPS_USER="root"
VPS_HOST="167.71.212.171"
SSH_KEY="~/2025wisuda"
SRC_DIR="$(dirname "$0")"  # Path to backend directory
DEST_DIR="/opt/backend/"     # Target directory on VPS

# Rsync with exclusions
rsync -avz \
  --exclude='venv' \
  --exclude='bahan' \
  --exclude='testing_ai_komprehensif' \
  --exclude='media' \
  --exclude='logs' \
  --exclude='staticfiles' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='*.pkl' \
  --exclude='*.log' \
  -e "ssh -i $SSH_KEY" \
  "$SRC_DIR/" "$VPS_USER@$VPS_HOST:$DEST_DIR"

# Print result
if [ $? -eq 0 ]; then
  echo "\n✅ Backend successfully deployed to $VPS_USER@$VPS_HOST:$DEST_DIR"
else
  echo "\n❌ Deployment failed. Please check your connection and SSH key."
fi 