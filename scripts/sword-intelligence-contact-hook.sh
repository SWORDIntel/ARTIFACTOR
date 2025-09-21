#!/bin/bash

# SWORD Intelligence Contact Information Hook System
# CONSTRUCTOR Agent - Standardized Repository Branding System
# Version: 1.0
# Purpose: Automatically adds/updates SWORD Intelligence contact information to README files
# Usage: ./sword-intelligence-contact-hook.sh [--apply] [--check] [--template]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR/..")"
README_FILE="$REPO_ROOT/README.md"
BACKUP_SUFFIX=".backup-$(date +%Y%m%d-%H%M%S)"

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

# Detect repository name from git remote or directory
detect_repository_name() {
    local repo_name=""

    # Try git remote first
    if git remote -v &>/dev/null; then
        repo_name=$(git remote get-url origin 2>/dev/null | sed -n 's|.*/\([^/]*\)\.git$|\1|p' | head -1)
    fi

    # Fallback to directory name
    if [[ -z "$repo_name" ]]; then
        repo_name=$(basename "$REPO_ROOT")
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

# Remove existing contact section
remove_existing_contact() {
    local temp_file=$(mktemp)

    # Remove everything from "## 📞 Contact & Support" to end of file
    awk '
        /^## 📞 Contact & Support/ { contact_section = 1 }
        /^---$/ && contact_section && prev_line == "" { contact_section = 1; next }
        !contact_section { print }
        /^---$/ && !contact_section { print; next }
        { prev_line = $0 }
    ' "$README_FILE" > "$temp_file"

    # Also remove old contact sections with different headers
    awk '
        /^## Contact & Support/ { contact_section = 1 }
        /^## Support/ { contact_section = 1 }
        /^## 🆘 Support/ { contact_section = 1 }
        !contact_section { print }
        /^$/ && contact_section { contact_section = 0 }
    ' "$temp_file" > "${temp_file}.2"

    mv "${temp_file}.2" "$temp_file"
    mv "$temp_file" "$README_FILE"
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

    # Backup existing README
    cp "$README_FILE" "${README_FILE}${BACKUP_SUFFIX}"
    log_info "Created backup: ${README_FILE}${BACKUP_SUFFIX}"

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

# Main function
main() {
    local repo_name=$(detect_repository_name)
    local action="${1:-check}"

    log_info "SWORD Intelligence Contact Hook System"
    log_info "Repository: $repo_name"
    log_info "Contact Email: ${repo_name}@swordintelligence.airforce"
    log_info "Domain: $SWORD_DOMAIN"
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
            install_git_hook
            ;;
        --help|-h)
            cat << EOF
SWORD Intelligence Contact Hook System

Usage: $0 [OPTIONS]

Options:
  --check, -c       Check if contact section is up to date
  --apply, -a       Apply/update contact section to README.md
  --template, -t    Show template for manual copying
  --install-hook, -i Install git pre-commit hook
  --help, -h        Show this help message

Examples:
  $0 --check        # Check current status
  $0 --apply        # Update README with contact info
  $0 --template     # Show template for manual use
  $0 --install-hook # Install git hook for automatic checking

Repository: $repo_name
Email: ${repo_name}@swordintelligence.airforce
Domain: $SWORD_DOMAIN
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