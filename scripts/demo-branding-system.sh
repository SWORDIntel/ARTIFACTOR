#!/bin/bash

# SWORD Intelligence Branding System Demo
# CONSTRUCTOR Agent - System Demonstration Script
# Version: 1.0
# Purpose: Demonstrate the complete branding system functionality

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Banner
print_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           SWORD Intelligence Branding System Demo            ║
║                                                               ║
║   🗡️  Demonstrating CONSTRUCTOR-level standardization       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Logging functions
log_header() {
    echo -e "\n${MAGENTA}=== $1 ===${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_demo() {
    echo -e "${YELLOW}[DEMO]${NC} $1"
}

# Demo repository detection
demo_repository_detection() {
    log_header "Repository Detection"

    log_demo "Detecting current repository information..."
    ./scripts/sword-intelligence-contact-hook.sh --check

    echo ""
    log_info "The system automatically detects:"
    echo "  • Repository name from Git remote URL"
    echo "  • Fallback to directory name if needed"
    echo "  • Converts to uppercase for email consistency"
    echo "  • Generates unique project email: ARTIFACTOR@swordintelligence.airforce"
}

# Demo template generation
demo_template_generation() {
    log_header "Contact Template Generation"

    log_demo "Generating standardized contact template..."
    echo ""
    ./scripts/sword-intelligence-contact-hook.sh --template

    echo ""
    log_info "Template features:"
    echo "  • Project-specific email address"
    echo "  • Consistent SWORD Intelligence branding"
    echo "  • Repository-specific GitHub links"
    echo "  • Professional formatting with emoji headers"
}

# Demo different repository examples
demo_repository_examples() {
    log_header "Multi-Repository Examples"

    log_demo "Simulating different repository configurations..."
    echo ""

    # Create temporary test scenarios
    local original_pwd=$(pwd)
    local temp_dir=$(mktemp -d)

    # Example 1: SHADOWGIT
    echo -e "${CYAN}Example 1: SHADOWGIT Repository${NC}"
    mkdir -p "$temp_dir/SHADOWGIT"
    cd "$temp_dir/SHADOWGIT"
    git init >/dev/null 2>&1
    git remote add origin https://github.com/SWORDIntel/SHADOWGIT.git >/dev/null 2>&1

    # Copy hook script
    mkdir -p scripts
    cp "$original_pwd/scripts/sword-intelligence-contact-hook.sh" scripts/

    echo "Repository: SHADOWGIT"
    echo "Email: SHADOWGIT@swordintelligence.airforce"
    echo "Repository URL: https://github.com/SWORDIntel/SHADOWGIT"
    echo ""

    # Example 2: CLAUDE-BACKUPS
    echo -e "${CYAN}Example 2: CLAUDE-BACKUPS Repository${NC}"
    mkdir -p "$temp_dir/CLAUDE-BACKUPS"
    cd "$temp_dir/CLAUDE-BACKUPS"
    git init >/dev/null 2>&1
    git remote add origin https://github.com/SWORDIntel/CLAUDE-BACKUPS.git >/dev/null 2>&1

    # Copy hook script
    mkdir -p scripts
    cp "$original_pwd/scripts/sword-intelligence-contact-hook.sh" scripts/

    echo "Repository: CLAUDE-BACKUPS"
    echo "Email: CLAUDE-BACKUPS@swordintelligence.airforce"
    echo "Repository URL: https://github.com/SWORDIntel/CLAUDE-BACKUPS"
    echo ""

    # Example 3: Directory name fallback
    echo -e "${CYAN}Example 3: Directory Name Fallback${NC}"
    mkdir -p "$temp_dir/MY-CUSTOM-PROJECT"
    cd "$temp_dir/MY-CUSTOM-PROJECT"

    # Copy hook script
    mkdir -p scripts
    cp "$original_pwd/scripts/sword-intelligence-contact-hook.sh" scripts/

    echo "Repository: MY-CUSTOM-PROJECT (no git remote)"
    echo "Email: MY-CUSTOM-PROJECT@swordintelligence.airforce"
    echo "Repository URL: https://github.com/SWORDIntel/MY-CUSTOM-PROJECT"

    # Cleanup
    cd "$original_pwd"
    rm -rf "$temp_dir"

    echo ""
    log_info "The system adapts to any repository structure automatically"
}

# Demo deployment methods
demo_deployment_methods() {
    log_header "Deployment Methods"

    log_demo "Available deployment options..."
    echo ""

    echo -e "${CYAN}Method 1: Global Installer (Remote)${NC}"
    echo "curl -fsSL https://raw.githubusercontent.com/SWORDIntel/ARTIFACTOR/main/scripts/install-sword-intelligence-branding.sh | bash"
    echo ""

    echo -e "${CYAN}Method 2: Local Installation${NC}"
    echo "git clone https://github.com/SWORDIntel/ARTIFACTOR.git"
    echo "cp ARTIFACTOR/scripts/install-sword-intelligence-branding.sh target-repo/"
    echo "cd target-repo && ./install-sword-intelligence-branding.sh"
    echo ""

    echo -e "${CYAN}Method 3: Manual Setup${NC}"
    echo "cp scripts/sword-intelligence-contact-hook.sh /target/repo/scripts/"
    echo "cd /target/repo"
    echo "./scripts/sword-intelligence-contact-hook.sh --apply"
    echo "./scripts/sword-intelligence-contact-hook.sh --install-hook"
    echo ""

    log_info "Choose the method that best fits your deployment workflow"
}

# Demo git hook functionality
demo_git_hooks() {
    log_header "Git Hook Integration"

    log_demo "Git hook system ensures automatic validation..."
    echo ""

    log_info "Pre-commit hook behavior:"
    echo "  1. Validates README contact section on each commit"
    echo "  2. Prompts for updates if information is outdated"
    echo "  3. Offers automatic application of changes"
    echo "  4. Stages updated README.md automatically"
    echo ""

    log_info "Git hook installed at: .git/hooks/pre-commit"
    echo ""

    echo -e "${CYAN}Example commit interaction:${NC}"
    echo '$ git commit -m "Update feature"'
    echo ""
    echo "README contact section needs updating."
    echo "Run: ./scripts/sword-intelligence-contact-hook.sh --apply"
    echo ""
    echo "Auto-apply now? (y/N) y"
    echo "Contact section updated and staged."
    echo "[main abc1234] Update feature"
}

# Demo system benefits
demo_system_benefits() {
    log_header "System Benefits"

    log_demo "CONSTRUCTOR-level standardization benefits..."
    echo ""

    echo -e "${CYAN}For Users:${NC}"
    echo "  ✓ Clear project-specific contact paths"
    echo "  ✓ Professional, consistent repository appearance"
    echo "  ✓ Easy navigation with standardized quick links"
    echo ""

    echo -e "${CYAN}For SWORD Intelligence:${NC}"
    echo "  ✓ Organized communication routing"
    echo "  ✓ Unified brand consistency across all repositories"
    echo "  ✓ Automated maintenance reduces overhead"
    echo "  ✓ Scalable management for unlimited repositories"
    echo ""

    echo -e "${CYAN}For Developers:${NC}"
    echo "  ✓ Zero maintenance overhead"
    echo "  ✓ One-command deployment"
    echo "  ✓ Automatic validation and updates"
    echo "  ✓ Flexible usage modes (check, apply, template)"
    echo ""

    log_success "Complete automation of repository branding across the organization"
}

# Demo commands
demo_available_commands() {
    log_header "Available Commands"

    log_demo "Hook script command reference..."
    echo ""

    echo -e "${CYAN}Primary Commands:${NC}"
    echo "  ./scripts/sword-intelligence-contact-hook.sh --check      # Validate current status"
    echo "  ./scripts/sword-intelligence-contact-hook.sh --apply      # Apply/update contact section"
    echo "  ./scripts/sword-intelligence-contact-hook.sh --template   # Show template for manual use"
    echo "  ./scripts/sword-intelligence-contact-hook.sh --install-hook # Install git pre-commit hook"
    echo "  ./scripts/sword-intelligence-contact-hook.sh --help       # Show detailed help"
    echo ""

    echo -e "${CYAN}Global Installer:${NC}"
    echo "  ./scripts/install-sword-intelligence-branding.sh          # Complete system installation"
    echo ""

    log_info "All commands include color-coded output and detailed status information"
}

# Main demo function
main() {
    print_banner

    log_info "Starting SWORD Intelligence Branding System demonstration"
    log_info "This demo shows the complete CONSTRUCTOR-level standardization system"
    echo ""

    # Run all demo sections
    demo_repository_detection
    demo_template_generation
    demo_repository_examples
    demo_deployment_methods
    demo_git_hooks
    demo_system_benefits
    demo_available_commands

    echo ""
    log_header "Demonstration Complete"
    echo ""
    log_success "SWORD Intelligence Branding System is ready for deployment"
    echo ""
    log_info "Next steps:"
    echo "  1. Deploy to other SWORD Intelligence repositories using global installer"
    echo "  2. Verify contact sections are applied consistently"
    echo "  3. Test git hooks ensure automatic maintenance"
    echo "  4. Monitor unique project emails for proper inquiry routing"
    echo ""
    log_info "System documentation: docs/SWORD_INTELLIGENCE_BRANDING_SYSTEM.md"
    log_info "Template reference: scripts/README-contact-template.md"
    echo ""

    echo -e "${GREEN}✓ CONSTRUCTOR Agent standardization system deployment complete${NC}"
}

# Execute main function
main "$@"