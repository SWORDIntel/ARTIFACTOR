# ARTIFACTOR Docker Setup

Complete Docker infrastructure for ARTIFACTOR - Simple Claude.ai artifact downloader.

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Build and run with clipboard access
docker-compose build
docker-compose run --rm artifactor --clipboard

# Other examples
docker-compose run --rm artifactor --url "https://example.com/artifact"
docker-compose run --rm artifactor --interactive
```

### Option 2: Using Makefile (Easy)

```bash
# Build image
make build

# Download from clipboard
make run

# Download from URL
make run-url URL="https://example.com/artifact"

# Interactive mode
make run-interactive

# Get shell access
make shell

# Show all commands
make help
```

### Option 3: Quick Script (Simple)

```bash
# Build and run with clipboard
./scripts/run-artifactor.sh --build --clipboard

# Shell access
./scripts/run-artifactor.sh --shell
```

## Docker Features

### Security Features
- **Non-root user**: Runs as `artifactor` user (not root)
- **Multi-stage build**: Optimized image size
- **Health checks**: Automatic container health monitoring
- **Resource limits**: Configurable CPU/memory limits

### Clipboard Support
- **X11 forwarding**: Full clipboard access on Linux
- **Multiple tools**: Both `xclip` and `xsel` installed
- **Fallback support**: Graceful degradation if clipboard unavailable

### Volume Management
- **Downloads volume**: `/app/downloads` mounted to host
- **Automatic creation**: Downloads directory created automatically
- **Proper permissions**: Files owned by correct user

## Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
# Edit .env as needed
```

Key variables:
- `DISPLAY`: X11 display for clipboard access
- `DEBUG`: Enable debug output
- `DOWNLOAD_TIMEOUT`: HTTP request timeout
- `OUTPUT_DIR`: Container downloads directory

### Docker Compose Override

For custom configurations:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
# Edit override file for custom settings
```

## Usage Examples

### Download from Clipboard
```bash
# Copy some code/text to clipboard first
docker-compose run --rm artifactor --clipboard
```

### Download from URL
```bash
docker-compose run --rm artifactor --url "https://gist.github.com/user/gist-id"
```

### Interactive Mode
```bash
docker-compose run --rm artifactor --interactive
# Paste content, then Ctrl+D
```

### Process File
```bash
# Place file in current directory
docker-compose run --rm -v "$(pwd)/input.txt:/app/input.txt" artifactor --file /app/input.txt
```

### Custom Output Directory
```bash
docker-compose run --rm -v "/path/to/custom:/app/downloads" artifactor --clipboard
```

## Advanced Usage

### Development Mode
```bash
# Mount source code for development
docker-compose run --rm -v "$(pwd):/app" artifactor --help
```

### Shell Access
```bash
# Get bash shell in container
docker-compose run --rm --entrypoint /bin/bash artifactor

# Or use Makefile
make shell
```

### Health Check
```bash
# Check container health
docker-compose run --rm artifactor health

# Or use Makefile
make health
```

### Debugging

Enable debug mode:
```bash
# Set in .env file
DEBUG=true

# Or pass as environment variable
docker-compose run --rm -e DEBUG=true artifactor --clipboard
```

View container logs:
```bash
make logs
```

## Troubleshooting

### Clipboard Issues

**Problem**: Clipboard doesn't work
**Solutions**:
1. Ensure X11 forwarding is working: `echo $DISPLAY`
2. Check X11 socket: `ls -la /tmp/.X11-unix/`
3. Try alternative: `xhost +local:docker` (temporary)

### Permission Issues

**Problem**: Cannot write to downloads directory
**Solutions**:
1. Check directory permissions: `ls -la downloads/`
2. Set correct ownership: `sudo chown -R $USER:$USER downloads/`
3. Use override file to set custom user ID

### Container Won't Start

**Problem**: Container fails to start
**Solutions**:
1. Check image exists: `docker images | grep artifactor`
2. Rebuild image: `make clean && make build`
3. Check logs: `docker-compose logs`

### Network Issues

**Problem**: Cannot download from URLs
**Solutions**:
1. Check internet connectivity in container
2. Check firewall/proxy settings
3. Try with `--network host` option

## Files Structure

```
ARTIFACTOR/
├── Dockerfile                          # Main Docker image
├── docker-compose.yml                  # Docker Compose configuration
├── docker-compose.override.yml.example # Override example
├── docker-entrypoint.sh               # Container entrypoint script
├── .dockerignore                       # Docker build ignore
├── .env.example                        # Environment variables example
├── Makefile                           # Build automation
├── scripts/
│   └── run-artifactor.sh              # Quick runner script
├── downloads/                         # Download output directory
└── simple-claude-downloader.py       # Main application
```

## Maintenance

### Cleanup
```bash
# Remove containers and images
make clean

# Clean downloads directory
make clean-downloads

# Full cleanup
docker system prune -a
```

### Updates
```bash
# Rebuild image with latest changes
make build

# Or force rebuild
docker-compose build --no-cache
```

### Monitoring
```bash
# Check running containers
docker ps

# Monitor resource usage
docker stats

# Health status
make health
```

## Performance Tips

1. **Use named volumes** for better I/O performance
2. **Limit resources** in docker-compose.override.yml
3. **Use .dockerignore** to reduce build context
4. **Multi-stage builds** already optimized for size

## Security Notes

- Container runs as non-root user `artifactor`
- Only necessary capabilities are granted
- Downloads directory is isolated
- No network services exposed by default
- Health checks prevent hanging containers

## Integration

### CI/CD Pipeline
```yaml
# Example GitHub Actions step
- name: Test ARTIFACTOR
  run: |
    make build
    make test
```

### Scripts Integration
```bash
#!/bin/bash
# Example integration script
./scripts/run-artifactor.sh --url "$ARTIFACT_URL"
```

This Docker setup provides a secure, easy-to-use, and production-ready environment for running the ARTIFACTOR Claude.ai artifact downloader.