#!/bin/bash

# SWORD Intelligence Repository Branding Installer
# CONSTRUCTOR Agent - Global Standardization System
# Version: 1.0
# Purpose: Install standardized SWORD Intelligence branding across all repositories
# Usage: curl -fsSL https://raw.githubusercontent.com/SWORDIntel/ARTIFACTOR/main/scripts/install-sword-intelligence-branding.sh | bash

set -euo pipefail

# Configuration
TEMP_DIR=$(mktemp -d)
HOOK_SCRIPT_URL="https://raw.githubusercontent.com/SWORDIntel/ARTIFACTOR/main/scripts/sword-intelligence-contact-hook.sh"
HOOK_SCRIPT_NAME="sword-intelligence-contact-hook.sh"
SCRIPTS_DIR="scripts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
print_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        SWORD Intelligence Repository Branding Installer      ║
║                                                               ║
║   🗡️  Standardizing contact information across all repos     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Cleanup function
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Not in a git repository. Please run this script from the root of a git repository."
        exit 1
    fi
}

# Detect repository information
detect_repo_info() {
    local repo_root=$(git rev-parse --show-toplevel)
    local repo_name=""

    # Try git remote first
    if git remote -v &>/dev/null; then
        repo_name=$(git remote get-url origin 2>/dev/null | sed -n 's|.*/\([^/]*\)\.git$|\1|p' | head -1)
    fi

    # Fallback to directory name
    if [[ -z "$repo_name" ]]; then
        repo_name=$(basename "$repo_root")
    fi

    # Convert to uppercase for email
    repo_name=$(echo "$repo_name" | tr '[:lower:]' '[:upper:]')

    echo "REPO_ROOT=$repo_root"
    echo "REPO_NAME=$repo_name"
    echo "CONTACT_EMAIL=${repo_name}@swordintelligence.airforce"
}

# Download hook script
download_hook_script() {
    local target_dir="$1"
    local target_file="$target_dir/$HOOK_SCRIPT_NAME"

    log_step "Downloading SWORD Intelligence contact hook script"

    # Create scripts directory if it doesn't exist
    mkdir -p "$target_dir"

    # Try to download from GitHub
    if command -v curl >/dev/null 2>&1; then
        if curl -fsSL "$HOOK_SCRIPT_URL" -o "$target_file"; then
            log_success "Downloaded hook script using curl"
        else
            log_warning "Failed to download from GitHub, using local fallback"
            return 1
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget -q "$HOOK_SCRIPT_URL" -O "$target_file"; then
            log_success "Downloaded hook script using wget"
        else
            log_warning "Failed to download from GitHub, using local fallback"
            return 1
        fi
    else
        log_warning "Neither curl nor wget available, using local fallback"
        return 1
    fi

    chmod +x "$target_file"
    return 0
}

# Create local hook script as fallback
create_local_hook_script() {
    local target_file="$1"

    log_step "Creating local hook script"

    cat > "$target_file" << 'EOF'
#!/bin/bash

# SWORD Intelligence Contact Information Hook System
# CONSTRUCTOR Agent - Standardized Repository Branding System
# Version: 1.0 (Local Fallback)

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
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Detect repository name
detect_repository_name() {
    local repo_name=""
    if git remote -v &>/dev/null; then
        repo_name=$(git remote get-url origin 2>/dev/null | sed -n 's|.*/\([^/]*\)\.git$|\1|p' | head -1)
    fi
    if [[ -z "$repo_name" ]]; then
        repo_name=$(basename "$REPO_ROOT")
    fi
    echo "$repo_name" | tr '[:lower:]' '[:upper:]'
}

# Generate contact section
generate_contact_section() {
    local repo_name="$1"
    local email="${repo_name}@swordintelligence.airforce"

cat << CONTACT_EOF

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

CONTACT_EOF
}

# Check contact section
check_contact_section() {
    local repo_name="$1"
    local expected_email="${repo_name}@swordintelligence.airforce"

    if [[ ! -f "$README_FILE" ]]; then
        log_warning "README.md not found"
        return 1
    fi

    if grep -q "📞 Contact & Support" "$README_FILE" &&
       grep -q "$expected_email" "$README_FILE" &&
       grep -q "$SWORD_DOMAIN" "$README_FILE"; then
        log_success "Contact section is up to date"
        return 0
    else
        log_warning "Contact section needs updating"
        return 1
    fi
}

# Apply contact section
apply_contact_section() {
    local repo_name="$1"

    if [[ ! -f "$README_FILE" ]]; then
        log_error "README.md not found"
        return 1
    fi

    cp "$README_FILE" "${README_FILE}${BACKUP_SUFFIX}"
    log_info "Created backup: ${README_FILE}${BACKUP_SUFFIX}"

    # Remove existing contact sections
    local temp_file=$(mktemp)
    awk '
        /^## 📞 Contact & Support/ { skip = 1; next }
        /^---$/ && skip { next }
        /^$/ && skip { skip = 0; next }
        !skip { print }
    ' "$README_FILE" > "$temp_file"

    mv "$temp_file" "$README_FILE"

    # Add new contact section
    generate_contact_section "$repo_name" >> "$README_FILE"
    log_success "Applied contact section"
}

# Main function
main() {
    local repo_name=$(detect_repository_name)
    local action="${1:-check}"

    case "$action" in
        --apply|-a) apply_contact_section "$repo_name" ;;
        --check|-c) check_contact_section "$repo_name" ;;
        *)
            check_contact_section "$repo_name"
            if [[ $? -ne 0 ]]; then
                log_info "Run '$0 --apply' to update README"
            fi
            ;;
    esac
}

main "$@"
EOF

    chmod +x "$target_file"
    log_success "Created local hook script"
}

# Install git hooks
install_git_hooks() {
    local repo_root="$1"
    local hook_script="$2"

    log_step "Installing git hooks"

    local pre_commit_hook="$repo_root/.git/hooks/pre-commit"

    # Create pre-commit hook
    cat > "$pre_commit_hook" << EOF
#!/bin/bash
# SWORD Intelligence Contact Information Pre-commit Hook
# Auto-generated by CONSTRUCTOR agent

HOOK_SCRIPT="$hook_script"

if [[ -f "\$HOOK_SCRIPT" ]]; then
    if ! "\$HOOK_SCRIPT" --check; then
        echo ""
        echo "README contact section needs updating."
        echo "Run: \$HOOK_SCRIPT --apply"
        echo ""
        echo "Auto-apply now? (y/N)"
        read -r response
        if [[ "\$response" =~ ^[Yy]$ ]]; then
            "\$HOOK_SCRIPT" --apply
            git add README.md
            echo "Contact section updated and staged."
        else
            echo "Commit aborted. Please update README contact section."
            exit 1
        fi
    fi
fi
EOF

    chmod +x "$pre_commit_hook"
    log_success "Installed pre-commit hook"
}

# Create documentation
create_documentation() {
    local repo_root="$1"
    local repo_name="$2"

    log_step "Creating documentation"

    local docs_dir="$repo_root/docs"
    mkdir -p "$docs_dir"

    cat > "$docs_dir/SWORD_INTELLIGENCE_BRANDING.md" << EOF
# SWORD Intelligence Repository Branding

This repository uses standardized SWORD Intelligence branding and contact information.

## Contact Information

- **Project Email**: ${repo_name}@swordintelligence.airforce
- **Organization**: SWORD Intelligence - Advanced AI & Software Solutions
- **Website**: https://swordintelligence.airforce
- **Repository**: https://github.com/SWORDIntel/${repo_name}

## Branding System

This repository includes automated branding management:

- **Hook Script**: \`scripts/sword-intelligence-contact-hook.sh\`
- **Git Hooks**: Pre-commit validation of contact information
- **Auto-update**: Contact section is automatically maintained

## Usage

\`\`\`bash
# Check contact section status
./scripts/sword-intelligence-contact-hook.sh --check

# Update contact section
./scripts/sword-intelligence-contact-hook.sh --apply

# View template
./scripts/sword-intelligence-contact-hook.sh --template
\`\`\`

## Maintenance

The contact information is automatically validated on each commit. If updates are needed, the pre-commit hook will prompt for automatic application.

To manually update the branding system:

\`\`\`bash
# Re-run the installer
curl -fsSL https://raw.githubusercontent.com/SWORDIntel/ARTIFACTOR/main/scripts/install-sword-intelligence-branding.sh | bash
\`\`\`

*This system ensures consistent branding across all SWORD Intelligence repositories.*
EOF

    log_success "Created branding documentation"
}

# Main installation function
main() {
    print_banner

    log_info "Starting SWORD Intelligence branding installation"

    # Check requirements
    check_git_repo

    # Get repository information
    eval $(detect_repo_info)
    log_info "Repository: $REPO_NAME"
    log_info "Root: $REPO_ROOT"
    log_info "Contact: $CONTACT_EMAIL"

    # Create target directory for scripts
    local target_scripts_dir="$REPO_ROOT/$SCRIPTS_DIR"
    local hook_script_path="$target_scripts_dir/$HOOK_SCRIPT_NAME"

    # Download or create hook script
    if ! download_hook_script "$target_scripts_dir"; then
        create_local_hook_script "$hook_script_path"
    fi

    # Install git hooks
    install_git_hooks "$REPO_ROOT" "$hook_script_path"

    # Create documentation
    create_documentation "$REPO_ROOT" "$REPO_NAME"

    # Apply contact section
    log_step "Applying contact section to README"
    if "$hook_script_path" --apply; then
        log_success "README updated with standardized contact information"
    else
        log_warning "Could not update README automatically"
    fi

    echo ""
    log_success "SWORD Intelligence branding installation complete!"
    echo ""
    log_info "Next steps:"
    echo "  1. Review the updated README.md"
    echo "  2. Commit the changes: git add . && git commit -m 'Add SWORD Intelligence branding'"
    echo "  3. The pre-commit hook will maintain contact information automatically"
    echo ""
    log_info "Hook script available at: $hook_script_path"
    log_info "Documentation at: $REPO_ROOT/docs/SWORD_INTELLIGENCE_BRANDING.md"
}

# Execute main function
main "$@"