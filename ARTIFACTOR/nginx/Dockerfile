# ARTIFACTOR Nginx - Reverse Proxy and Load Balancer
# High-performance reverse proxy with SSL termination and caching

FROM nginx:1.25-alpine

# Metadata
LABEL maintainer="ARTIFACTOR Team" \
      description="ARTIFACTOR v3.0 Nginx Reverse Proxy" \
      version="3.0.0"

# Install additional packages
RUN apk add --no-cache \
    curl \
    bash \
    openssl \
    ca-certificates \
    # For SSL certificate generation
    certbot \
    certbot-nginx \
    # For monitoring and health checks
    wget \
    # For log processing
    logrotate

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/conf.d/ /etc/nginx/conf.d/

# Copy SSL certificates (if any)
COPY nginx/ssl/ /etc/nginx/ssl/

# Copy health check script
COPY nginx/scripts/healthcheck.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/healthcheck.sh

# Copy certificate generation script
COPY nginx/scripts/generate-ssl.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-ssl.sh

# Create necessary directories
RUN mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    mkdir -p /var/cache/nginx/fastcgi_temp && \
    mkdir -p /var/cache/nginx/uwsgi_temp && \
    mkdir -p /var/cache/nginx/scgi_temp && \
    mkdir -p /var/log/nginx && \
    mkdir -p /etc/nginx/ssl && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/ssl

# Generate self-signed certificate for development
RUN /usr/local/bin/generate-ssl.sh

# Create nginx user and set permissions
RUN chown -R nginx:nginx /etc/nginx && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Expose ports
EXPOSE 80 443

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]