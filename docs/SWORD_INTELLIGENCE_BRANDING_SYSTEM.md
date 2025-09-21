# SWORD Intelligence Repository Branding System

**CONSTRUCTOR Agent Implementation - Standardized Contact Management**

## Overview

This system provides automated, standardized contact information management across all SWORD Intelligence repositories. It ensures every repository has consistent, professional branding with unique, project-specific contact emails.

## System Architecture

```
SWORD Intelligence Branding System
├── Hook Script (sword-intelligence-contact-hook.sh)
│   ├── Repository Detection
│   ├── Contact Section Generation
│   ├── README.md Management
│   └── Git Hook Integration
├── Global Installer (install-sword-intelligence-branding.sh)
│   ├── Remote Deployment
│   ├── Local Fallback
│   └── Documentation Generation
└── Template System (README-contact-template.md)
    ├── Standardized Format
    ├── Dynamic Variables
    └── Consistent Branding
```

## Core Features

### 1. Automatic Repository Detection
- Detects repository name from Git remote URL
- Fallback to directory name if Git remote unavailable
- Converts repository name to uppercase for email consistency

### 2. Dynamic Email Generation
- Format: `REPONAME@swordintelligence.airforce`
- Examples:
  - ARTIFACTOR → `ARTIFACTOR@swordintelligence.airforce`
  - SHADOWGIT → `SHADOWGIT@swordintelligence.airforce`
  - CLAUDE-BACKUPS → `CLAUDE-BACKUPS@swordintelligence.airforce`

### 3. Standardized Contact Section
- Professional formatting with emoji headers
- Consistent organization branding
- Project-specific quick links
- Security reporting guidance

### 4. Git Hook Integration
- Pre-commit validation of contact information
- Automatic prompting for updates when needed
- Optional auto-application of changes

### 5. Cross-Repository Deployment
- Single-command installation across all repositories
- Remote deployment via curl/wget
- Local fallback for offline environments

## Installation Methods

### Method 1: Global Installer (Recommended)
```bash
# From any SWORD Intelligence repository
curl -fsSL https://raw.githubusercontent.com/SWORDIntel/ARTIFACTOR/main/scripts/install-sword-intelligence-branding.sh | bash
```

### Method 2: Local Installation
```bash
# Clone ARTIFACTOR repository
git clone https://github.com/SWORDIntel/ARTIFACTOR.git
cd target-repository

# Copy and run installer
cp /path/to/ARTIFACTOR/scripts/install-sword-intelligence-branding.sh .
./install-sword-intelligence-branding.sh
```

### Method 3: Manual Setup
```bash
# Copy hook script to target repository
cp scripts/sword-intelligence-contact-hook.sh /target/repo/scripts/
cd /target/repo

# Apply contact section
./scripts/sword-intelligence-contact-hook.sh --apply

# Install git hooks
./scripts/sword-intelligence-contact-hook.sh --install-hook
```

## Usage Commands

### Hook Script Operations
```bash
# Check if contact section is current
./scripts/sword-intelligence-contact-hook.sh --check

# Apply/update contact section
./scripts/sword-intelligence-contact-hook.sh --apply

# Show template for manual copying
./scripts/sword-intelligence-contact-hook.sh --template

# Install git pre-commit hook
./scripts/sword-intelligence-contact-hook.sh --install-hook

# Show help
./scripts/sword-intelligence-contact-hook.sh --help
```

### Global Installer Options
```bash
# Standard installation
./install-sword-intelligence-branding.sh

# The installer automatically:
# 1. Downloads latest hook script from GitHub
# 2. Creates local fallback if download fails
# 3. Installs git hooks
# 4. Applies contact section
# 5. Creates documentation
```

## File Structure

After installation, repositories will have:

```
repository-root/
├── scripts/
│   └── sword-intelligence-contact-hook.sh    # Main hook script
├── docs/
│   └── SWORD_INTELLIGENCE_BRANDING.md        # Project documentation
├── .git/hooks/
│   └── pre-commit                            # Git hook for validation
└── README.md                                 # Updated with contact section
```

## Template Format

The standardized contact section added to all README files:

```markdown
---

## 📞 Contact & Support

**Project Email**: REPONAME@swordintelligence.airforce
**Organization**: SWORD Intelligence - Advanced AI & Software Solutions
**Website**: https://swordintelligence.airforce
**Repository**: https://github.com/SWORDIntel/REPONAME

For project-specific inquiries, technical support, or collaboration opportunities, please use the project email above. This ensures your message reaches the right team and gets proper context about the REPONAME project.

### Quick Links
- **Issues & Bug Reports**: [GitHub Issues](https://github.com/SWORDIntel/REPONAME/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/SWORDIntel/REPONAME/discussions)
- **Documentation**: [Project Wiki](https://github.com/SWORDIntel/REPONAME/wiki)
- **Security Reports**: Please use the project email for security-related concerns

*Developed by SWORD Intelligence - Advancing the frontiers of AI and software solutions*
```

## Git Hook Behavior

The pre-commit hook automatically:

1. **Validates Contact Section**: Checks if README has current contact information
2. **Prompts for Updates**: If outdated, offers to auto-apply changes
3. **Interactive Mode**: User can choose to apply now or abort commit
4. **Auto-staging**: Applied changes are automatically staged for commit

Example pre-commit interaction:
```bash
$ git commit -m "Update feature"

README contact section needs updating.
Run: ./scripts/sword-intelligence-contact-hook.sh --apply

Auto-apply now? (y/N) y
Contact section updated and staged.
[main abc1234] Update feature
```

## Repository Examples

### ARTIFACTOR
- **Email**: ARTIFACTOR@swordintelligence.airforce
- **Purpose**: Claude.ai artifact management with PyGUI interface
- **Repository**: https://github.com/SWORDIntel/ARTIFACTOR

### SHADOWGIT (Hypothetical)
- **Email**: SHADOWGIT@swordintelligence.airforce
- **Purpose**: Advanced Git operations with intelligence features
- **Repository**: https://github.com/SWORDIntel/SHADOWGIT

### CLAUDE-BACKUPS (Hypothetical)
- **Email**: CLAUDE-BACKUPS@swordintelligence.airforce
- **Purpose**: Claude agent framework backup systems
- **Repository**: https://github.com/SWORDIntel/CLAUDE-BACKUPS

## Benefits

### For Users
- **Clear Contact Path**: Know exactly where to send project-specific inquiries
- **Professional Appearance**: Consistent, polished repository presentation
- **Easy Navigation**: Standardized quick links to issues, discussions, wiki

### For SWORD Intelligence
- **Organized Communication**: Project-specific emails route inquiries correctly
- **Brand Consistency**: Unified appearance across all repositories
- **Automated Maintenance**: Git hooks ensure contact information stays current
- **Scalable Management**: Single system manages hundreds of repositories

### For Developers
- **Zero Maintenance**: Contact information updates automatically
- **Easy Deployment**: One command installs across all repositories
- **Flexible Usage**: Check, apply, or template modes for different needs

## Maintenance

### Updating the System
To update the branding system across all repositories:

1. **Update Master Scripts**: Modify scripts in ARTIFACTOR repository
2. **Global Deployment**: Each repository can pull latest version:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/SWORDIntel/ARTIFACTOR/main/scripts/install-sword-intelligence-branding.sh | bash
   ```

### Organization Changes
If SWORD Intelligence branding changes:

1. **Update Configuration**: Modify `SWORD_DOMAIN` and `SWORD_ORGANIZATION` in hook script
2. **Redeploy**: Run installer across all repositories
3. **Automatic Propagation**: Git hooks ensure changes apply on next commit

### Repository Migration
When moving repositories:

1. **Update Remote**: Git remote URL change is automatically detected
2. **Re-run Installer**: Applies new repository name and links
3. **Commit Changes**: Updated contact information is committed

## Security Features

- **Input Validation**: All repository names and URLs are sanitized
- **Backup Creation**: README.md is backed up before modification
- **Safe Defaults**: Uses localhost binding and secure defaults
- **Permission Handling**: Automatic permission management for scripts

## Error Handling

The system includes comprehensive error handling:

- **Network Failures**: Falls back to local script creation
- **Git Repository Detection**: Validates Git repository before operation
- **File Permissions**: Automatically sets correct executable permissions
- **Backup Recovery**: Failed operations can be reverted from backups

## Integration with CONSTRUCTOR Agent

This branding system is designed as a CONSTRUCTOR agent implementation:

- **Standardization Focus**: Creates consistent patterns across all projects
- **Automation Priority**: Minimizes manual maintenance overhead
- **Professional Quality**: Ensures enterprise-grade repository presentation
- **Scalable Architecture**: Supports unlimited repository count
- **Template-Driven**: Consistent output through centralized templates

## Future Enhancements

Potential improvements to the branding system:

1. **Multi-Language Support**: Template translations for international projects
2. **Custom Branding**: Per-project customization while maintaining consistency
3. **Analytics Integration**: Track contact email usage and effectiveness
4. **Advanced Git Hooks**: Post-commit, pre-push validation
5. **CI/CD Integration**: Automated branding validation in continuous integration

---

*This documentation describes the complete SWORD Intelligence Repository Branding System as implemented by the CONSTRUCTOR agent for standardized contact management across all SWORD Intelligence repositories.*