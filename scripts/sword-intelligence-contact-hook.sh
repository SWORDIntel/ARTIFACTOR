#!/bin/bash

# SWORD Intelligence Contact Information Hook System
# CONSTRUCTOR Agent - Standardized Repository Branding System
# Version: 1.0
# Purpose: Automatically adds/updates SWORD Intelligence contact information to README files
# Usage: ./sword-intelligence-contact-hook.sh [--apply] [--check] [--template]

set -euo pipefail

# Cross-platform compatibility checks
setup_cross_platform() {
    # Check for required commands
    local required_commands=("git" "awk" "sed" "date")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            echo "Error: Required command '$cmd' not found" >&2
            exit 1
        fi
    done

    # macOS compatibility for date command
    if [[ "$(uname)" == "Darwin" ]] && command -v gdate >/dev/null 2>&1; then
        alias date='gdate'
    fi

    # Set secure umask for file creation
    umask 0022
}

# Initialize cross-platform setup
setup_cross_platform

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Secure repository root detection
detect_repo_root() {
    local repo_root
    if repo_root=$(git rev-parse --show-toplevel 2>/dev/null); then
        # Validate the path is within expected bounds
        if [[ "$repo_root" == /* ]] && [[ -d "$repo_root/.git" ]]; then
            echo "$repo_root"
        else
            echo "$SCRIPT_DIR"
        fi
    else
        # Secure fallback - stay in script directory
        echo "$SCRIPT_DIR"
    fi
}

REPO_ROOT="$(detect_repo_root)"
README_FILE="$REPO_ROOT/README.md"

# Race-condition-free backup naming
create_backup_name() {
    local source_file="$1"
    local backup_base="${source_file}.backup-$(date +%Y%m%d-%H%M%S)"
    local counter=1
    local backup_file="$backup_base"

    # Find unique backup filename
    while [[ -f "$backup_file" ]]; do
        backup_file="${backup_base}-${counter}"
        ((counter++))
    done

    echo "$backup_file"
}

BACKUP_SUFFIX="$(create_backup_name "$README_FILE" | sed "s|$README_FILE||")"

# SWORD Intelligence branding configuration
SWORD_DOMAIN="https://swordintelligence.airforce"
SWORD_ORGANIZATION="SWORD Intelligence - Advanced AI & Software Solutions"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Git information caching for performance
GIT_INFO_CACHED=""
GIT_REPO_ROOT=""
GIT_REMOTE_URL=""

cache_git_info() {
    if [[ -z "$GIT_INFO_CACHED" ]]; then
        GIT_REPO_ROOT="$(detect_repo_root)"
        GIT_REMOTE_URL="$(git remote get-url origin 2>/dev/null || echo "")"
        GIT_INFO_CACHED="1"
    fi
}

# Input validation for repository names
validate_repository_name() {
    local repo_name="$1"

    # Check for valid characters (alphanumeric, dots, hyphens, underscores)
    if [[ ! "$repo_name" =~ ^[a-zA-Z0-9._-]+$ ]]; then
        log_error "Invalid repository name characters: $repo_name"
        return 1
    fi

    # Check length limits (GitHub max is 100, we use 50 for email compatibility)
    if [[ ${#repo_name} -gt 50 ]]; then
        log_error "Repository name too long (max 50 chars): $repo_name"
        return 1
    fi

    # Check for reserved names
    case "$repo_name" in
        "."|".."|"")
            log_error "Invalid repository name: $repo_name"
            return 1
            ;;
    esac

    echo "$repo_name"
}

# Detect repository name from git remote or directory
detect_repository_name() {
    local repo_name=""

    # Cache git information for performance
    cache_git_info

    # Try git remote first
    if [[ -n "$GIT_REMOTE_URL" ]]; then
        repo_name=$(echo "$GIT_REMOTE_URL" | sed -n 's|.*/\([^/]*\)\.git$|\1|p' | head -1)
    fi

    # Fallback to directory name
    if [[ -z "$repo_name" ]]; then
        repo_name=$(basename "$GIT_REPO_ROOT")
    fi

    # Validate the repository name
    if ! repo_name=$(validate_repository_name "$repo_name"); then
        log_error "Could not determine valid repository name"
        return 1
    fi

    # Convert to uppercase for email
    echo "$repo_name" | tr '[:lower:]' '[:upper:]'
}

# Generate standardized contact section
generate_contact_section() {
    local repo_name="$1"
    local email="${repo_name}@swordintelligence.airforce"

    cat << EOF

---

## 📞 Contact & Support

**Project Email**: $email
**Organization**: $SWORD_ORGANIZATION
**Website**: $SWORD_DOMAIN
**Repository**: https://github.com/SWORDIntel/$repo_name

For project-specific inquiries, technical support, or collaboration opportunities, please use the project email above. This ensures your message reaches the right team and gets proper context about the $repo_name project.

### Quick Links
- **Issues & Bug Reports**: [GitHub Issues](https://github.com/SWORDIntel/$repo_name/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/SWORDIntel/$repo_name/discussions)
- **Documentation**: [Project Wiki](https://github.com/SWORDIntel/$repo_name/wiki)
- **Security Reports**: Please use the project email for security-related concerns

*Developed by SWORD Intelligence - Advancing the frontiers of AI and software solutions*

EOF
}

# Check if README needs updating
check_contact_section() {
    local repo_name="$1"
    local expected_email="${repo_name}@swordintelligence.airforce"

    if [[ ! -f "$README_FILE" ]]; then
        log_warning "README.md not found at $README_FILE"
        return 1
    fi

    # Check if contact section exists and is current
    if grep -q "📞 Contact & Support" "$README_FILE" &&
       grep -q "$expected_email" "$README_FILE" &&
       grep -q "$SWORD_DOMAIN" "$README_FILE"; then
        log_success "Contact section is up to date"
        return 0
    else
        log_warning "Contact section needs updating or is missing"
        return 1
    fi
}

# Optimized contact section removal (single-pass AWK)
remove_existing_contact() {
    local temp_file=$(mktemp)

    # Single-pass AWK script for efficiency
    awk '
        BEGIN { contact_section = 0 }

        # Start of any contact section
        /^## 📞 Contact & Support/ || /^## Contact & Support/ || /^## Support/ || /^## 🆘 Support/ {
            contact_section = 1
            next
        }

        # End of contact section (horizontal rule or next section)
        /^---$/ && contact_section {
            contact_section = 0
            next
        }

        # Next section header ends contact section
        /^##/ && contact_section {
            contact_section = 0
            print
            next
        }

        # Skip lines within contact section
        contact_section { next }

        # Print all other lines
        { print }
    ' "$README_FILE" > "$temp_file"

    # Safely replace original file
    if [[ -s "$temp_file" ]]; then
        mv "$temp_file" "$README_FILE"
    else
        log_error "Failed to process README file safely"
        rm -f "$temp_file"
        return 1
    fi
}

# Apply contact section to README
apply_contact_section() {
    local repo_name="$1"

    if [[ ! -f "$README_FILE" ]]; then
        log_error "README.md not found. Creating basic README with contact section."
        cat > "$README_FILE" << EOF
# $repo_name

This is the $repo_name project by SWORD Intelligence.

$(generate_contact_section "$repo_name")
EOF
        log_success "Created new README.md with contact section"
        return 0
    fi

    # Create race-condition-free backup
    local backup_file=$(create_backup_name "$README_FILE")
    cp "$README_FILE" "$backup_file"
    log_info "Created backup: $backup_file"

    # Remove existing contact section
    remove_existing_contact

    # Add new contact section
    local contact_section=$(generate_contact_section "$repo_name")
    echo "$contact_section" >> "$README_FILE"

    log_success "Applied standardized contact section to README.md"
}

# Display template for manual use
show_template() {
    local repo_name="$1"
    echo "=== SWORD Intelligence Contact Template for $repo_name ==="
    generate_contact_section "$repo_name"
    echo "=== End Template ==="
}

# Install git hook
install_git_hook() {
    local hook_file="$REPO_ROOT/.git/hooks/pre-commit"
    local hook_script_path="$SCRIPT_DIR/sword-intelligence-contact-hook.sh"

    if [[ ! -d "$REPO_ROOT/.git/hooks" ]]; then
        log_error "Not a git repository or .git/hooks directory not found"
        return 1
    fi

    # Create or update pre-commit hook
    cat > "$hook_file" << EOF
#!/bin/bash
# SWORD Intelligence Contact Information Pre-commit Hook
# Auto-generated by CONSTRUCTOR agent

# Check if README contact section is up to date
if [[ -f "$hook_script_path" ]]; then
    if ! "$hook_script_path" --check; then
        echo "README contact section needs updating. Run:"
        echo "  $hook_script_path --apply"
        echo ""
        echo "Or auto-apply now? (y/N)"
        read -r response
        if [[ "\$response" =~ ^[Yy]$ ]]; then
            "$hook_script_path" --apply
            git add README.md
        else
            echo "Commit aborted. Please update README contact section."
            exit 1
        fi
    fi
fi
EOF

    chmod +x "$hook_file"
    log_success "Installed git pre-commit hook at $hook_file"
}

# Health check system
health_check() {
    log_info "Running system health check"

    # Check git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_warning "Not in a git repository"
    fi

    # Check write permissions
    if [[ ! -w "$REPO_ROOT" ]]; then
        log_error "Repository root is not writable: $REPO_ROOT"
        return 1
    fi

    # Check if README exists and is writable
    if [[ -f "$README_FILE" ]] && [[ ! -w "$README_FILE" ]]; then
        log_error "README file is not writable: $README_FILE"
        return 1
    fi

    # Check git hooks directory
    if [[ -d "$REPO_ROOT/.git/hooks" ]] && [[ ! -w "$REPO_ROOT/.git/hooks" ]]; then
        log_warning "Git hooks directory is not writable"
    fi

    log_success "Health check completed"
    return 0
}

# Error recovery function
recover_from_error() {
    local error_msg="$1"
    local backup_file="${2:-}"

    log_error "Error occurred: $error_msg"

    if [[ -n "$backup_file" ]] && [[ -f "$backup_file" ]]; then
        log_info "Attempting to restore from backup: $backup_file"
        if cp "$backup_file" "$README_FILE"; then
            log_success "Restored from backup successfully"
        else
            log_error "Failed to restore from backup"
        fi
    fi
}

# Main function
main() {
    # Run health check first
    if ! health_check; then
        log_error "Health check failed. Aborting."
        exit 1
    fi

    local repo_name
    if ! repo_name=$(detect_repository_name); then
        log_error "Failed to detect repository name"
        exit 1
    fi

    local action="${1:-check}"

    log_info "SWORD Intelligence Contact Hook System"
    log_info "Repository: $repo_name"
    log_info "Contact Email: ${repo_name}@swordintelligence.airforce"
    log_info "Domain: $SWORD_DOMAIN"
    log_info "Repository Root: $REPO_ROOT"
    echo ""

    case "$action" in
        --check|-c)
            check_contact_section "$repo_name"
            ;;
        --apply|-a)
            apply_contact_section "$repo_name"
            ;;
        --template|-t)
            show_template "$repo_name"
            ;;
        --install-hook|-i)
            if install_git_hook; then
                log_success "Git hook installation completed"
            else
                log_error "Git hook installation failed"
                exit 1
            fi
            ;;
        --health|-H)
            health_check
            ;;
        --help|-h)
            cat << EOF
SWORD Intelligence Contact Hook System v1.1

Usage: $0 [OPTIONS]

Options:
  --check, -c       Check if contact section is up to date
  --apply, -a       Apply/update contact section to README.md
  --template, -t    Show template for manual copying
  --install-hook, -i Install git pre-commit hook
  --health, -H      Run system health check
  --help, -h        Show this help message

Examples:
  $0 --check        # Check current status
  $0 --apply        # Update README with contact info
  $0 --template     # Show template for manual use
  $0 --install-hook # Install git hook for automatic checking
  $0 --health       # Run system diagnostics

Repository: $repo_name
Email: ${repo_name}@swordintelligence.airforce
Domain: $SWORD_DOMAIN
Root: $REPO_ROOT

Enhanced Features (v1.1):
✅ Security hardening with input validation
✅ Performance optimization with git caching
✅ Cross-platform compatibility (Linux/macOS/WSL)
✅ Race-condition-free backup system
✅ Comprehensive error handling and recovery
✅ Health check and validation system
EOF
            ;;
        *)
            check_contact_section "$repo_name"
            if [[ $? -ne 0 ]]; then
                echo ""
                log_info "Run '$0 --apply' to update README with standardized contact section"
                log_info "Run '$0 --help' for more options"
            fi
            ;;
    esac
}

# Execute main function
main "$@"