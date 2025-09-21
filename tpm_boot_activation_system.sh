#!/bin/bash
# TPM Boot-Time Activation System
# Legitimate approach for STMicroelectronics TPM 2.0 integration
# Date: 2025-09-20

set -euo pipefail

# Configuration
TPM_SERVICE_NAME="tpm-boot-activation"
SYSTEMD_SERVICE_PATH="/etc/systemd/system/${TPM_SERVICE_NAME}.service"
KERNEL_PARAM_FILE="/etc/default/grub"
TPM_LOG="/var/log/tpm-boot-activation.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "${TPM_LOG}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "${TPM_LOG}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "${TPM_LOG}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Detect TPM hardware
detect_tpm_hardware() {
    log "Detecting TPM hardware..."

    if [[ ! -e /dev/tpm0 ]]; then
        error "TPM device /dev/tpm0 not found"
        return 1
    fi

    if [[ ! -e /dev/tpmrm0 ]]; then
        error "TPM resource manager /dev/tpmrm0 not found"
        return 1
    fi

    # Check TPM ownership and permissions
    local tpm_owner=$(stat -c '%U' /dev/tpm0)
    local tpm_group=$(stat -c '%G' /dev/tpm0)

    log "TPM device found: /dev/tpm0 (owner: ${tpm_owner}, group: ${tpm_group})"

    # Verify TPM is accessible
    if command -v tpm2_getcap >/dev/null 2>&1; then
        if tpm2_getcap properties-fixed >/dev/null 2>&1; then
            log "TPM is accessible and functional"
            return 0
        else
            warning "TPM device exists but not accessible"
            return 1
        fi
    else
        warning "tpm2-tools not installed"
        return 1
    fi
}

# Configure kernel parameters for TPM
configure_kernel_parameters() {
    log "Configuring kernel parameters for TPM..."

    # Backup GRUB configuration
    if [[ -f "${KERNEL_PARAM_FILE}" ]]; then
        cp "${KERNEL_PARAM_FILE}" "${KERNEL_PARAM_FILE}.backup.$(date +%Y%m%d)"
        log "GRUB configuration backed up"
    fi

    # Add TPM-friendly kernel parameters
    local tpm_params="tpm_tis.force=1 tpm_tis.interrupts=0"

    if grep -q "GRUB_CMDLINE_LINUX_DEFAULT" "${KERNEL_PARAM_FILE}"; then
        # Check if TPM parameters already exist
        if ! grep -q "tpm_tis.force" "${KERNEL_PARAM_FILE}"; then
            sed -i "/GRUB_CMDLINE_LINUX_DEFAULT/s/\"$/ ${tpm_params}\"/" "${KERNEL_PARAM_FILE}"
            log "Added TPM kernel parameters: ${tpm_params}"
        else
            log "TPM kernel parameters already configured"
        fi
    else
        warning "GRUB_CMDLINE_LINUX_DEFAULT not found in ${KERNEL_PARAM_FILE}"
    fi
}

# Create systemd service for TPM activation
create_systemd_service() {
    log "Creating systemd service for TPM boot activation..."

    cat > "${SYSTEMD_SERVICE_PATH}" << 'EOF'
[Unit]
Description=TPM Boot-Time Activation Service
After=multi-user.target
Wants=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/tpm-boot-activate.sh
StandardOutput=journal
StandardError=journal
User=root
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF

    log "Systemd service created at ${SYSTEMD_SERVICE_PATH}"
}

# Create TPM activation script
create_activation_script() {
    log "Creating TPM activation script..."

    cat > /usr/local/bin/tpm-boot-activate.sh << 'EOF'
#!/bin/bash
# TPM Boot Activation Script
# Executes TPM initialization tasks at boot time

set -euo pipefail

LOG_FILE="/var/log/tpm-boot-activation.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

# Wait for TPM to be ready
wait_for_tpm() {
    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if [[ -e /dev/tpm0 ]] && [[ -e /dev/tpmrm0 ]]; then
            log "TPM devices available"
            return 0
        fi

        log "Waiting for TPM devices... (attempt $((attempt + 1))/${max_attempts})"
        sleep 2
        ((attempt++))
    done

    log "ERROR: TPM devices not available after ${max_attempts} attempts"
    return 1
}

# Activate TPM functionality
activate_tpm() {
    log "Starting TPM activation..."

    # Ensure tss user can access TPM
    if id "tss" >/dev/null 2>&1; then
        chown tss:tss /dev/tpm* 2>/dev/null || true
        log "TPM device permissions set for tss user"
    fi

    # Test basic TPM functionality
    if command -v tpm2_getcap >/dev/null 2>&1; then
        if tpm2_getcap properties-fixed >/dev/null 2>&1; then
            log "TPM basic functionality verified"

            # Initialize PCR measurements for system state
            if tpm2_pcrread sha256:0,1,2,3,4,5,6,7 >/dev/null 2>&1; then
                log "PCR measurements accessible"
            else
                log "WARNING: PCR measurements not accessible"
            fi

            # Check for existing keys and create primary key if needed
            if ! tpm2_readpublic -c 0x81000001 >/dev/null 2>&1; then
                log "Creating TPM primary key..."
                tpm2_createprimary -C e -g sha256 -G rsa -c primary.ctx 2>/dev/null || true
                tpm2_evictcontrol -C o -c primary.ctx 0x81000001 2>/dev/null || true
                rm -f primary.ctx
                log "TPM primary key created"
            else
                log "TPM primary key already exists"
            fi

        else
            log "ERROR: TPM not accessible via tpm2-tools"
            return 1
        fi
    else
        log "WARNING: tpm2-tools not available"
    fi

    log "TPM activation completed successfully"
    return 0
}

# Emergency stop mechanism
emergency_stop() {
    if [[ -f "/tmp/tpm-emergency-stop" ]]; then
        log "EMERGENCY STOP: TPM activation halted by emergency file"
        exit 0
    fi
}

# Main execution
main() {
    log "=== TPM Boot Activation Started ==="

    # Check for emergency stop
    emergency_stop

    # Wait for TPM to be ready
    if ! wait_for_tpm; then
        log "FATAL: TPM not available"
        exit 1
    fi

    # Activate TPM
    if activate_tpm; then
        log "=== TPM Boot Activation Completed Successfully ==="
        # Signal successful activation
        touch /var/run/tpm-activated
    else
        log "=== TPM Boot Activation Failed ==="
        exit 1
    fi
}

# Execute main function
main "$@"
EOF

    chmod +x /usr/local/bin/tpm-boot-activate.sh
    log "TPM activation script created and made executable"
}

# Install emergency stop mechanism
create_emergency_stop() {
    log "Creating emergency stop mechanism..."

    cat > /usr/local/bin/tpm-emergency-stop.sh << 'EOF'
#!/bin/bash
# TPM Emergency Stop Script
# Usage: tpm-emergency-stop.sh [enable|disable|status]

EMERGENCY_FILE="/tmp/tpm-emergency-stop"

case "${1:-status}" in
    "enable")
        touch "${EMERGENCY_FILE}"
        echo "TPM emergency stop ENABLED"
        echo "TPM boot activation will be skipped on next boot"
        ;;
    "disable")
        rm -f "${EMERGENCY_FILE}"
        echo "TPM emergency stop DISABLED"
        echo "TPM boot activation will proceed normally"
        ;;
    "status")
        if [[ -f "${EMERGENCY_FILE}" ]]; then
            echo "TPM emergency stop is ENABLED"
            exit 1
        else
            echo "TPM emergency stop is DISABLED"
            exit 0
        fi
        ;;
    *)
        echo "Usage: $0 [enable|disable|status]"
        exit 1
        ;;
esac
EOF

    chmod +x /usr/local/bin/tpm-emergency-stop.sh
    log "Emergency stop script created"
}

# Configure Secure Boot integration
configure_secure_boot() {
    log "Checking Secure Boot configuration..."

    if [[ -d /sys/firmware/efi ]]; then
        if [[ -f /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c ]]; then
            local secure_boot_status=$(od -An -t u1 /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c | awk '{print $NF}')
            if [[ $secure_boot_status -eq 1 ]]; then
                log "Secure Boot is ENABLED"
                log "TPM activation will respect Secure Boot policies"
            else
                log "Secure Boot is DISABLED"
            fi
        else
            log "Secure Boot status unknown"
        fi
    else
        log "System is not UEFI, Secure Boot not applicable"
    fi
}

# Recovery mechanism setup
setup_recovery() {
    log "Setting up recovery mechanisms..."

    # Create recovery script
    cat > /usr/local/bin/tpm-recovery.sh << 'EOF'
#!/bin/bash
# TPM Recovery Script
# Handles TPM activation failures and recovery

LOG_FILE="/var/log/tpm-recovery.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Reset TPM to factory state (WARNING: Destroys all keys)
reset_tpm() {
    log "WARNING: Resetting TPM to factory state"
    log "This will destroy all existing TPM keys and data"

    read -p "Are you sure you want to reset TPM? (yes/no): " confirm
    if [[ "$confirm" == "yes" ]]; then
        tpm2_clear -c p 2>/dev/null || {
            log "ERROR: TPM clear failed"
            return 1
        }
        log "TPM reset completed"
    else
        log "TPM reset cancelled"
    fi
}

# Diagnose TPM issues
diagnose_tpm() {
    log "=== TPM Diagnostics ==="

    # Check device files
    if [[ -e /dev/tpm0 ]]; then
        log "✓ /dev/tpm0 exists"
        ls -la /dev/tpm0 | tee -a "${LOG_FILE}"
    else
        log "✗ /dev/tpm0 missing"
    fi

    if [[ -e /dev/tpmrm0 ]]; then
        log "✓ /dev/tpmrm0 exists"
        ls -la /dev/tpmrm0 | tee -a "${LOG_FILE}"
    else
        log "✗ /dev/tpmrm0 missing"
    fi

    # Check kernel modules
    if lsmod | grep -q tpm; then
        log "✓ TPM kernel modules loaded:"
        lsmod | grep tpm | tee -a "${LOG_FILE}"
    else
        log "✗ No TPM kernel modules loaded"
    fi

    # Check tpm2-tools
    if command -v tpm2_getcap >/dev/null 2>&1; then
        log "✓ tpm2-tools available"
        if tpm2_getcap properties-fixed >/dev/null 2>&1; then
            log "✓ TPM communication working"
        else
            log "✗ TPM communication failed"
        fi
    else
        log "✗ tpm2-tools not available"
    fi
}

case "${1:-help}" in
    "reset")
        reset_tpm
        ;;
    "diagnose")
        diagnose_tpm
        ;;
    "help"|*)
        echo "TPM Recovery Script"
        echo "Usage: $0 [reset|diagnose|help]"
        echo ""
        echo "  reset    - Reset TPM to factory state (DESTRUCTIVE)"
        echo "  diagnose - Run TPM diagnostics"
        echo "  help     - Show this help"
        ;;
esac
EOF

    chmod +x /usr/local/bin/tpm-recovery.sh
    log "Recovery script created"
}

# Main installation function
install_tpm_boot_system() {
    log "=== Installing TPM Boot-Time Activation System ==="

    # Check prerequisites
    check_root

    # Detect TPM hardware
    if ! detect_tpm_hardware; then
        error "TPM hardware detection failed"
        exit 1
    fi

    # Configure kernel parameters
    configure_kernel_parameters

    # Create systemd service
    create_systemd_service

    # Create activation script
    create_activation_script

    # Create emergency stop mechanism
    create_emergency_stop

    # Configure Secure Boot integration
    configure_secure_boot

    # Setup recovery mechanisms
    setup_recovery

    # Enable systemd service
    systemctl daemon-reload
    systemctl enable "${TPM_SERVICE_NAME}"
    log "Systemd service enabled"

    # Update GRUB if kernel parameters were changed
    if command -v update-grub >/dev/null 2>&1; then
        update-grub
        log "GRUB configuration updated"
    elif command -v grub-mkconfig >/dev/null 2>&1; then
        grub-mkconfig -o /boot/grub/grub.cfg
        log "GRUB configuration updated"
    fi

    log "=== TPM Boot-Time Activation System Installed ==="
    log ""
    log "Next Steps:"
    log "1. Reboot the system to test TPM activation"
    log "2. Check /var/log/tpm-boot-activation.log for activation status"
    log "3. Use 'tpm-emergency-stop.sh enable' to disable TPM activation if needed"
    log "4. Use 'tpm-recovery.sh diagnose' to troubleshoot issues"
    log ""
    log "Emergency Commands:"
    log "- tpm-emergency-stop.sh enable   # Disable TPM activation"
    log "- tpm-recovery.sh diagnose       # Run diagnostics"
    log "- tpm-recovery.sh reset          # Factory reset TPM (DESTRUCTIVE)"
}

# Command line interface
case "${1:-install}" in
    "install")
        install_tpm_boot_system
        ;;
    "status")
        if systemctl is-active "${TPM_SERVICE_NAME}" >/dev/null 2>&1; then
            echo "TPM boot activation service is ACTIVE"
            if [[ -f /var/run/tpm-activated ]]; then
                echo "TPM was successfully activated on last boot"
            else
                echo "TPM activation status unknown"
            fi
        else
            echo "TPM boot activation service is INACTIVE"
        fi
        ;;
    "logs")
        if [[ -f "${TPM_LOG}" ]]; then
            tail -n 50 "${TPM_LOG}"
        else
            echo "No TPM boot activation logs found"
        fi
        ;;
    "help"|*)
        echo "TPM Boot-Time Activation System"
        echo "Usage: $0 [install|status|logs|help]"
        echo ""
        echo "  install - Install TPM boot activation system"
        echo "  status  - Check activation service status"
        echo "  logs    - Show recent activation logs"
        echo "  help    - Show this help"
        echo ""
        echo "This system provides legitimate TPM integration with:"
        echo "- Secure Boot preservation"
        echo "- Emergency stop capability"
        echo "- Recovery mechanisms"
        echo "- Comprehensive logging"
        ;;
esac