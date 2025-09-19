# Portainer CE Custom Build
# DOCKER-AGENT: Enterprise-grade container management for Etherscan API
FROM portainer/portainer-ce:2.20.3-alpine

# Metadata
LABEL maintainer="DOCKER-AGENT" \
      description="Portainer CE with custom configuration for Etherscan API management" \
      version="2.20.3-custom" \
      project="etherscan-docker-stack"

# Create directories for custom configurations
USER root
RUN apk add --no-cache \
    curl \
    jq \
    ca-certificates \
    openssl \
    && rm -rf /var/cache/apk/*

# Create custom directories
RUN mkdir -p /opt/portainer/config \
             /opt/portainer/templates \
             /opt/portainer/ssl \
             /opt/portainer/backup \
             /opt/portainer/logs

# Copy custom configuration files
COPY config/portainer-config.json /opt/portainer/config/
COPY config/templates.json /opt/portainer/templates/
COPY config/ssl/ /opt/portainer/ssl/
COPY scripts/backup.sh /opt/portainer/backup/
COPY scripts/healthcheck.sh /opt/portainer/

# Set proper permissions
RUN chmod +x /opt/portainer/backup/backup.sh \
    && chmod +x /opt/portainer/healthcheck.sh \
    && chown -R 1000:1000 /opt/portainer

# Switch back to portainer user
USER 1000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /opt/portainer/healthcheck.sh

# Expose Portainer port (9000) and HTTPS port (9443)
EXPOSE 9000 9443

# Set environment variables for customization
ENV PORTAINER_ADMIN_PASSWORD_FILE=/opt/portainer/config/admin_password \
    PORTAINER_SSL_CERT=/opt/portainer/ssl/portainer.crt \
    PORTAINER_SSL_KEY=/opt/portainer/ssl/portainer.key \
    PORTAINER_TEMPLATES_URL=file:///opt/portainer/templates/templates.json

# Custom entrypoint arguments
ENTRYPOINT ["/portainer"]
CMD ["--admin-password-file", "/opt/portainer/config/admin_password", \
     "--ssl", \
     "--sslcert", "/opt/portainer/ssl/portainer.crt", \
     "--sslkey", "/opt/portainer/ssl/portainer.key", \
     "--templates", "file:///opt/portainer/templates/templates.json", \
     "--logo", "https://raw.githubusercontent.com/portainer/portainer/develop/app/assets/images/logo_alt.png"]