# Deployment Guide — Multi-Objective Optimization GUI

## Option 1 — Run locally (simplest)

**Requirements:** Python 3.8+

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python main.py
```

Open `http://localhost:8080` in your browser.

Default login credentials pre-configured:
- **Admin**: `admin@example.com` / `AdminPassword123!`
- **User**: `test@test.com` / `TestPassword123!`
- *Or click "Register" to create a new user account directly.*

---

## Option 2 — Docker (recommended for sharing / deployment)

**Requirements:** Docker Desktop (or Docker Engine on Linux)

```bash
# Build the image
docker build -t moo-gui .

# Run the container
docker run -p 8080:8080 moo-gui
```

Open `http://localhost:8080`.

### Persist data between restarts

Mount the `database/`, `experiments/`, and `exports/` folders as volumes so
user accounts and saved experiments survive container restarts:

```bash
docker run -p 8080:8080 \
  -v "%cd%/database:/app/database" \
  -v "%cd%/experiments:/app/experiments" \
  -v "%cd%/exports:/app/exports" \
  moo-gui
```

*(On Linux/macOS replace `%cd%` with `$(pwd)`)*

---

## Option 3 — Docker Compose

Create a `docker-compose.yml` next to the `BTP/` folder:

```yaml
version: "3.9"
services:
  moo-gui:
    build: ./BTP
    ports:
      - "8080:8080"
    volumes:
      - ./BTP/database:/app/database
      - ./BTP/experiments:/app/experiments
      - ./BTP/exports:/app/exports
    environment:
      # Optional overrides
      # MOO_GUI_DEBUG: "false"
      # MOO_GUI_PORT: "8080"
    restart: unless-stopped
```

```bash
docker compose up --build
```

---

## Option 4 — Deploy to a cloud VM (e.g. AWS EC2, Azure VM, DigitalOcean)

1. SSH into your server and install Docker.
2. Copy the `BTP/` folder to the server (scp, git clone, etc.).
3. Run the Docker commands from Option 2/3 above.
4. Open port **8080** in your cloud firewall / security group.
5. Access via `http://<server-ip>:8080`.

To run behind a domain with HTTPS, put **nginx** or **Caddy** in front:

```nginx
# /etc/nginx/sites-available/moo-gui
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Environment variables

The app reads these at startup (all optional — hardcoded defaults apply if absent):

| Variable | Default | Description |
|---|---|---|
| `MOO_GUI_HOST` | `0.0.0.0` | Bind address |
| `MOO_GUI_PORT` | `8080` | Port (set in `main.py`) |
| `MOO_GUI_DEBUG` | `false` | Enable Dash debug mode |
| `MOO_GUI_MEMORY_LIMIT` | `2048` | Memory limit in MB |
| `MOO_GUI_TIMEOUT` | `60` | Optimization timeout in minutes |

---

## OCR / Equation upload (optional)

The equation-upload feature requires Tesseract OCR. It is disabled by default.
To enable it:

1. Install Tesseract:
   - Windows: download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `apt-get install tesseract-ocr`
2. Uncomment the `Pillow` and `pytesseract` lines in `requirements.txt`.
3. Re-install: `pip install -r requirements.txt`

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'yaml'` | `pip install pyyaml==6.0.1` |
| `ModuleNotFoundError: No module named 'pymoo'` | `pip install pymoo==0.6.1.3` |
| Port 8080 already in use | Change port in `main.py` line 15 |
| `database/users.json` not found | The file is created automatically on first registration |
| White screen / JS error | Clear browser cache and hard-reload (`Ctrl+Shift+R`) |
