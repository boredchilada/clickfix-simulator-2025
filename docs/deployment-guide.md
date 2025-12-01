# Deployment & Multi-Domain Setup

This guide covers how to deploy the ClickFix Training Tool in a production environment and how to configure it for multi-domain operations.

## Production Deployment

For production, we recommend running the application behind a reverse proxy like **Caddy** or **Nginx**. This handles SSL/TLS termination (HTTPS) and allows you to serve the application on standard ports (80/443).

### Why HTTPS is Critical
The ClickFix attack relies on the `navigator.clipboard.writeText()` API. Modern browsers **block** this API on insecure origins (HTTP). You **must** serve the application over HTTPS (or localhost) for the trap to work.

### Port Configuration Note
By default, the application (`run.py` and `docker-compose.yml`) listens on port **443** to support standalone HTTPS.

When using a reverse proxy, you have two options:
1.  **Map Ports:** Change `docker-compose.yml` to map the container's 443 to a local port (e.g., `5000:443`).
2.  **Change App Port:** Modify `run.py` to listen on 5000.

The examples below assume the application is accessible internally at `localhost:5000`.

### Option A: Caddy (Recommended)
Caddy is the easiest option as it automatically handles SSL certificates from Let's Encrypt.

**Caddyfile:**
```caddyfile
training.yourdomain.com {
    reverse_proxy localhost:5000
}
```

### Option B: Nginx
Standard Nginx configuration with Certbot.

```nginx
server {
    listen 443 ssl;
    server_name training.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/training.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/training.yourdomain.com/privkey.pem;

    location / {
        # Proxy to the internal port (ensure app is running on 5000 or map 5000:443 in docker)
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Multi-Domain Setup

You may want to use different domains for different campaigns to increase realism (e.g., `secure-login.com` for a login lure and `update-browser.net` for a browser trap).

Since the ClickFix tool is a single Flask application, you can handle this at the **Reverse Proxy** level.

### Strategy: One App, Multiple Domains

You point all your domains to the same server IP. The reverse proxy listens for all of them and forwards traffic to the single Flask instance running on port 5000.

#### Caddy Configuration
```caddyfile
# Domain 1: Corporate Login Lure
login.secure-update.com {
    reverse_proxy localhost:5000
}

# Domain 2: Browser Update Lure
chrome-update.net {
    reverse_proxy localhost:5000
}

# Domain 3: Admin Dashboard
# This domain will serve the app, but you can use Caddy to restrict access or redirect root to /admin
admin.training-internal.com {
    # Optional: Restrict to internal IP range
    # @internal {
    #     remote_ip 10.0.0.0/8 192.168.0.0/16
    # }
    # handle @internal {
    #     reverse_proxy localhost:5000
    # }

    # Redirect root to /admin for convenience
    redir / /admin

    reverse_proxy localhost:5000
}
```

**Note on Protection:** The application itself protects the `/admin` route with Basic Authentication (configured via `ADMIN_USERNAME` and `ADMIN_PASSWORD`). The reverse proxy configuration above allows you to add an additional layer of security, such as IP allowlisting or VPN-only access.

#### Nginx Configuration
You can use a single `server` block with multiple server names, or separate blocks if you need different SSL certs.

```nginx
server {
    listen 443 ssl;
    server_name login.secure-update.com chrome-update.net admin.training-internal.com;
    
    # ... SSL config ...

    location / {
        proxy_pass http://127.0.0.1:5000;
        # ... proxy headers ...
    }
}
```

### Handling Campaigns per Domain

The Flask app itself doesn't strictly enforce "Domain A must show Campaign A". However, you can structure your links to match the domain.

1.  **Create Campaigns:**
    *   Create Campaign "Login" -> Slug: `/s/login`
    *   Create Campaign "Update" -> Slug: `/s/update`

2.  **Distribute Links:**
    *   Send `https://login.secure-update.com/s/login` to targets.
    *   Send `https://chrome-update.net/s/update` to targets.

Even though `https://login.secure-update.com/s/update` would technically work, users are unlikely to discover it.

### Advanced: Domain-Specific Routing (Middleware)

If you strictly want `domain-a.com` to *only* serve Campaign A, you would need to implement middleware in the Flask app or logic in your reverse proxy to rewrite paths.

**Nginx Rewrite Example:**
If you want the root URL `https://chrome-update.net/` to automatically show the update trap without the `/s/update` path:

```nginx
server {
    server_name chrome-update.net;
    location / {
        # Rewrite root to the specific campaign slug
        rewrite ^/$ /s/update break;
        proxy_pass http://127.0.0.1:5000;
    }
}
```

This allows you to have clean, realistic URLs like `https://chrome-update.net/` that serve the specific content immediately.