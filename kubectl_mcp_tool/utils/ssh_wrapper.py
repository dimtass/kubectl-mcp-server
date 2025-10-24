#!/usr/bin/env python3
"""
SSH command wrapper for remote kubectl/helm execution.

This module provides a centralized way to execute kubectl and helm commands
either locally or via SSH to a remote host, based on environment variables.
"""

import os
import logging
import shlex
from typing import List, Optional

logger = logging.getLogger(__name__)


class SSHCommandWrapper:
    """
    Wrapper class for executing commands locally or via SSH.

    Environment Variables:
        KUBECTL_SSH_ENABLED: Enable SSH mode (true/false, default: false)
        KUBECTL_SSH_USER: SSH username (required if SSH enabled)
        KUBECTL_SSH_HOST: SSH host IP/hostname (required if SSH enabled)
        KUBECTL_SSH_PORT: SSH port (optional, default: 22)
        KUBECTL_SSH_KEY: Path to SSH private key (optional)
    """

    def __init__(self):
        """Initialize the SSH wrapper with configuration from environment variables."""
        self.ssh_enabled = os.environ.get('KUBECTL_SSH_ENABLED', 'false').lower() in ('true', '1', 'yes')
        self.ssh_user = os.environ.get('KUBECTL_SSH_USER', '')
        self.ssh_host = os.environ.get('KUBECTL_SSH_HOST', '')
        self.ssh_port = os.environ.get('KUBECTL_SSH_PORT', '22')
        self.ssh_key = os.environ.get('KUBECTL_SSH_KEY', '')

        # Validate configuration if SSH is enabled
        if self.ssh_enabled:
            self._validate_config()
            logger.info(f"SSH mode enabled: {self.ssh_user}@{self.ssh_host}:{self.ssh_port}")
        else:
            logger.debug("SSH mode disabled - executing commands locally")

    def _validate_config(self) -> None:
        """
        Validate SSH configuration.

        Raises:
            ValueError: If required configuration is missing
        """
        if not self.ssh_user:
            raise ValueError(
                "KUBECTL_SSH_USER environment variable is required when SSH mode is enabled"
            )
        if not self.ssh_host:
            raise ValueError(
                "KUBECTL_SSH_HOST environment variable is required when SSH mode is enabled"
            )

        # Validate SSH key path if provided
        if self.ssh_key and not os.path.exists(os.path.expanduser(self.ssh_key)):
            logger.warning(f"SSH key file not found: {self.ssh_key}")

    def wrap_command(self, cmd: List[str]) -> List[str]:
        """
        Wrap a command for SSH execution if SSH mode is enabled.

        Args:
            cmd: Command as a list of strings (e.g., ['kubectl', 'get', 'pods'])

        Returns:
            Wrapped command list for subprocess execution

        Examples:
            Local mode:
                ['kubectl', 'get', 'pods'] -> ['kubectl', 'get', 'pods']

            SSH mode:
                ['kubectl', 'get', 'pods'] -> ['ssh', 'user@host', 'kubectl get pods']
        """
        if not self.ssh_enabled:
            return cmd

        # Build the SSH command
        ssh_cmd = ['ssh']

        # Add port if not default
        if self.ssh_port and self.ssh_port != '22':
            ssh_cmd.extend(['-p', self.ssh_port])

        # Add SSH key if specified
        if self.ssh_key:
            expanded_key = os.path.expanduser(self.ssh_key)
            ssh_cmd.extend(['-i', expanded_key])

        # Add common SSH options for better compatibility
        ssh_cmd.extend([
            '-o', 'StrictHostKeyChecking=no',  # Auto-accept host keys (consider security implications)
            '-o', 'UserKnownHostsFile=/dev/null',  # Don't save host keys
            '-o', 'LogLevel=ERROR',  # Reduce SSH verbosity
        ])

        # Add user@host
        ssh_cmd.append(f'{self.ssh_user}@{self.ssh_host}')

        # Properly quote the remote command
        # Join command parts and escape them properly for SSH
        remote_command = ' '.join(shlex.quote(arg) for arg in cmd)
        ssh_cmd.append(remote_command)

        logger.debug(f"Wrapped command: {' '.join(ssh_cmd)}")
        return ssh_cmd

    def wrap_shell_command(self, cmd: str) -> str:
        """
        Wrap a shell command string for SSH execution if SSH mode is enabled.

        This is used for commands that are executed with shell=True in subprocess.

        Args:
            cmd: Command as a string (e.g., 'kubectl get pods | grep Running')

        Returns:
            Wrapped command string

        Examples:
            Local mode:
                'kubectl get pods' -> 'kubectl get pods'

            SSH mode:
                'kubectl get pods' -> 'ssh user@host "kubectl get pods"'
        """
        if not self.ssh_enabled:
            return cmd

        # Build SSH command prefix
        ssh_prefix = 'ssh'

        # Add port if not default
        if self.ssh_port and self.ssh_port != '22':
            ssh_prefix += f' -p {self.ssh_port}'

        # Add SSH key if specified
        if self.ssh_key:
            expanded_key = os.path.expanduser(self.ssh_key)
            ssh_prefix += f' -i {shlex.quote(expanded_key)}'

        # Add common SSH options
        ssh_prefix += ' -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR'

        # Build full command
        wrapped_cmd = f'{ssh_prefix} {self.ssh_user}@{self.ssh_host} {shlex.quote(cmd)}'

        logger.debug(f"Wrapped shell command: {wrapped_cmd}")
        return wrapped_cmd

    @property
    def is_enabled(self) -> bool:
        """Check if SSH mode is enabled."""
        return self.ssh_enabled

    def get_connection_info(self) -> dict:
        """
        Get SSH connection information.

        Returns:
            Dictionary with connection details
        """
        return {
            'enabled': self.ssh_enabled,
            'user': self.ssh_user if self.ssh_enabled else None,
            'host': self.ssh_host if self.ssh_enabled else None,
            'port': self.ssh_port if self.ssh_enabled else None,
            'key': self.ssh_key if self.ssh_enabled else None,
        }


# Global singleton instance
_ssh_wrapper_instance: Optional[SSHCommandWrapper] = None


def get_ssh_wrapper() -> SSHCommandWrapper:
    """
    Get the global SSH wrapper instance (singleton pattern).

    Returns:
        SSHCommandWrapper instance
    """
    global _ssh_wrapper_instance
    if _ssh_wrapper_instance is None:
        _ssh_wrapper_instance = SSHCommandWrapper()
    return _ssh_wrapper_instance


def reset_ssh_wrapper() -> None:
    """
    Reset the global SSH wrapper instance.

    This is useful for testing or when environment variables change.
    """
    global _ssh_wrapper_instance
    _ssh_wrapper_instance = None
