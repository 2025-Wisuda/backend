#!/bin/bash
# Setup nginx config for backend.2025wisuda.me
# Usage: sudo ./nginx_setup.sh

set -e

NGINX_CONF_PATH="/etc/nginx/sites-available/backend.2025wisuda.me"
NGINX_SYMLINK_PATH="/etc/nginx/sites-enabled/backend.2025wisuda.me"

# Write nginx config
cat > "$NGINX_CONF_PATH" <<EOF
server {
    server_name backend.2025wisuda.me;

    location / {
        proxy_pass http://localhost:8899;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/ai.2025wisuda.me/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/ai.2025wisuda.me/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    client_max_body_size 20M;
    location /media/ {
        alias /opt/backend/media/;
    }
}
server {
    if ($host = backend.2025wisuda.me) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    server_name backend.2025wisuda.me;
    return 404; # managed by Certbot
}
EOF

# Symlink to sites-enabled if not already
if [ ! -L "$NGINX_SYMLINK_PATH" ]; then
    ln -s "$NGINX_CONF_PATH" "$NGINX_SYMLINK_PATH"
fi

# Test nginx config
if nginx -t; then
    systemctl reload nginx
    echo -e "\n✅ Nginx config applied and reloaded successfully."
else
    echo -e "\n❌ Nginx config test failed. Please check the config manually."
    exit 1
fi 