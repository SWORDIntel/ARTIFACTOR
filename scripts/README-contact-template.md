# SWORD Intelligence Repository Contact Template

This file shows the exact format that will be applied to all SWORD Intelligence repositories.

## Template Format

The following contact section will be automatically added to the end of every README.md:

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

## Dynamic Variables

The template system automatically replaces:

- `REPONAME` → Actual repository name (uppercase)
- Repository-specific URLs and links
- Consistent branding across all projects

## Examples

### For ARTIFACTOR repository:
- Email: `ARTIFACTOR@swordintelligence.airforce`
- Repository: `https://github.com/SWORDIntel/ARTIFACTOR`

### For SHADOWGIT repository:
- Email: `SHADOWGIT@swordintelligence.airforce`
- Repository: `https://github.com/SWORDIntel/SHADOWGIT`

### For CLAUDE-BACKUPS repository:
- Email: `CLAUDE-BACKUPS@swordintelligence.airforce`
- Repository: `https://github.com/SWORDIntel/CLAUDE-BACKUPS`

## Implementation

This template is automatically applied by:

1. **Hook Script**: `scripts/sword-intelligence-contact-hook.sh`
2. **Git Hooks**: Pre-commit validation ensures consistency
3. **Global Installer**: One-command deployment across repositories

## Benefits

- **Unique Project Emails**: Each repository gets its own contact email
- **Consistent Branding**: Standardized format across all SWORD Intelligence projects
- **Automatic Maintenance**: Git hooks ensure contact information stays current
- **Professional Appearance**: Unified look and feel for all repositories
- **Easy Updates**: Centralized system allows for organization-wide updates

*This standardization ensures professional, consistent contact information across the entire SWORD Intelligence ecosystem.*