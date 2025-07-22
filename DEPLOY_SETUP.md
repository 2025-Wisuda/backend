# Backend Deployment Guide (Production)

This guide explains how to deploy the backend to a production VPS using Docker and Nginx. Follow each step carefully for a secure and reliable deployment.

---

## 1. Prerequisites
- A VPS (Ubuntu 20.04+ recommended)
- Docker & Docker Compose installed on the VPS
- Nginx installed on the VPS
- A domain/subdomain (e.g. `backend.yourdomain.com`) pointing to your VPS IP
- SSH key access to the VPS
- (Optional) SSL certificates (Let's Encrypt recommended)

> **Note:** Replace all example domains, IPs, and usernames with your own values.

---

## 2. Upload Backend Code to VPS

From your local machine, run the deployment script to upload the backend code to the VPS, excluding unnecessary files:

```bash
cd /path/to/backend
./deploy_to_vps.sh
```
- This will upload the backend to `/opt/backend` on your VPS.
- The script uses `rsync` and excludes folders like `venv`, `bahan`, `media`, `logs`, etc.
- Edit `deploy_to_vps.sh` if you need to change the VPS IP, SSH key, or destination path.

---

## 3. Set Permissions for Media Directory

On the VPS, ensure the media directory is owned by the web server user (usually `www-data`):

```bash
sudo chown -R www-data:www-data /opt/backend/media
sudo find /opt/backend/media -type d -exec chmod 755 {} \;
sudo find /opt/backend/media -type f -exec chmod 644 {} \;
```

---

## 4. Deploy Backend with Docker Compose

On the VPS, run the deployment script to build and start the backend services:

```bash
cd /opt/backend
chmod +x deploy.sh
./deploy.sh
```
- This will stop any running containers, rebuild the images, and start the backend and database.
- You can safely run this script multiple times for updates or redeployments.

---

## 5. Set Up Nginx Reverse Proxy

Run the provided script to configure Nginx for your backend domain:

```bash
cd /opt/backend
sudo chmod +x nginx_setup.sh
sudo ./nginx_setup.sh
```
- This will write the Nginx config to `/etc/nginx/sites-available/backend.yourdomain.com` and enable it.
- The config proxies HTTPS traffic to the backend container and serves media files directly.
- **Edit the script or config if your domain, SSL certificate path, or backend path is different!**

---

## 6. (Optional) Set Up SSL Certificates

If you don't have SSL certificates yet, use Let's Encrypt:

```bash
sudo apt update && sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d backend.yourdomain.com --non-interactive --agree-tos --email your@email.com
```
- Update the Nginx config if your certificate paths are different.

---

## 7. Verify Deployment

- Visit `https://backend.yourdomain.com/admin/` in your browser. You should see the Django admin login page.
- Test media file access, e.g. `https://backend.yourdomain.com/media/room_booking_documents/.../yourfile.pdf`
- Check container status:
  ```bash
  cd /opt/backend
  docker-compose ps
  ```
- Check Nginx status:
  ```bash
  sudo systemctl status nginx
  sudo tail -n 50 /var/log/nginx/error.log
  ```

---

## 8. Notes & Customization
- **Always update domain names, IP addresses, and email addresses to match your environment.**
- If you use a different backend path, update all scripts and Nginx config accordingly.
- For additional security, set up a firewall (UFW), disable root SSH login, and keep your system updated.
- For database backups, consider automating `mysqldump` or using Docker volume backups.

---

## 9. Useful Scripts in `/opt/backend`
- `deploy_to_vps.sh` — Upload backend code to VPS (run locally)
- `deploy.sh` — Build and start backend services (run on VPS)
- `nginx_setup.sh` — Configure Nginx for backend domain (run on VPS)
- `clear-cache.sh` — Clear Django cache (run on VPS)
- `run_local.sh` — For local development only

---

**Deployment complete!**

If you encounter issues, check the logs, verify permissions, and ensure all paths and domains are correct. 