# SSH Remote Execution Configuration

This guide explains how to configure kubectl-mcp-server to execute kubectl and helm commands on a remote host via SSH instead of locally.

## Overview

By default, kubectl-mcp-server executes kubectl and helm commands locally. With SSH mode enabled, all commands are transparently executed on a remote host via SSH, allowing you to:

- Run the MCP server on one machine while accessing a Kubernetes cluster on another
- Avoid installing kubectl/helm locally
- Centralize cluster access through a bastion/jump host
- Manage remote clusters without direct network access

## Environment Variables

Configure SSH mode using the following environment variables:

### Required Variables (when SSH is enabled)

| Variable | Description | Example |
|----------|-------------|---------|
| `KUBECTL_SSH_ENABLED` | Enable SSH mode | `true`, `1`, `yes`, or `false` (default) |
| `KUBECTL_SSH_USER` | SSH username | `dimtass` |
| `KUBECTL_SSH_HOST` | SSH host IP or hostname | `192.168.1.130` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `KUBECTL_SSH_PORT` | SSH port | `22` | `2222` |
| `KUBECTL_SSH_KEY` | Path to SSH private key | None | `~/.ssh/id_rsa` |

## Setup Instructions

### 1. Basic Setup (Password Authentication)

```bash
# Set environment variables
export KUBECTL_SSH_ENABLED=true
export KUBECTL_SSH_USER=dimtass
export KUBECTL_SSH_HOST=192.168.1.130

# Start the MCP server
python run_server.py
```

**Note:** Password authentication will prompt for a password on each command execution, which is not recommended for automated use.

### 2. Key-Based Authentication (Recommended)

#### Generate SSH Key (if you don't have one)

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/kubectl_mcp_key
```

#### Copy Public Key to Remote Host

```bash
ssh-copy-id -i ~/.ssh/kubectl_mcp_key.pub dimtass@192.168.1.130
```

#### Test SSH Connection

```bash
ssh -i ~/.ssh/kubectl_mcp_key dimtass@192.168.1.130 "kubectl version --client"
```

#### Configure Environment

```bash
export KUBECTL_SSH_ENABLED=true
export KUBECTL_SSH_USER=dimtass
export KUBECTL_SSH_HOST=192.168.1.130
export KUBECTL_SSH_KEY=~/.ssh/kubectl_mcp_key
```

### 3. Using a Non-Standard SSH Port

```bash
export KUBECTL_SSH_ENABLED=true
export KUBECTL_SSH_USER=dimtass
export KUBECTL_SSH_HOST=192.168.1.130
export KUBECTL_SSH_PORT=2222
export KUBECTL_SSH_KEY=~/.ssh/kubectl_mcp_key
```

## Configuration Files

### For Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "kubectl": {
      "command": "python",
      "args": ["/path/to/kubectl-mcp-server/run_server.py"],
      "env": {
        "KUBECTL_SSH_ENABLED": "true",
        "KUBECTL_SSH_USER": "dimtass",
        "KUBECTL_SSH_HOST": "192.168.1.130",
        "KUBECTL_SSH_KEY": "/Users/youruser/.ssh/kubectl_mcp_key"
      }
    }
  }
}
```

### For Cursor

Add to your Cursor settings:

```json
{
  "mcp": {
    "servers": {
      "kubectl": {
        "command": "python",
        "args": ["/path/to/kubectl-mcp-server/run_server.py"],
        "env": {
          "KUBECTL_SSH_ENABLED": "true",
          "KUBECTL_SSH_USER": "dimtass",
          "KUBECTL_SSH_HOST": "192.168.1.130",
          "KUBECTL_SSH_KEY": "/home/youruser/.ssh/kubectl_mcp_key"
        }
      }
    }
  }
}
```

### Using Docker

```bash
docker run -it \
  -e KUBECTL_SSH_ENABLED=true \
  -e KUBECTL_SSH_USER=dimtass \
  -e KUBECTL_SSH_HOST=192.168.1.130 \
  -e KUBECTL_SSH_KEY=/root/.ssh/id_rsa \
  -v ~/.ssh:/root/.ssh:ro \
  kubectl-mcp-server
```

## Remote Host Requirements

The remote host must have:

1. **kubectl** installed and configured with access to your Kubernetes cluster
2. **helm** (optional, if you plan to use Helm operations)
3. **SSH server** running and accessible
4. **Proper kubeconfig** file (usually at `~/.kube/config`)

### Verify Remote Setup

```bash
# Test kubectl access
ssh dimtass@192.168.1.130 "kubectl cluster-info"

# Test helm (if needed)
ssh dimtass@192.168.1.130 "helm version"

# Verify kubeconfig
ssh dimtass@192.168.1.130 "kubectl config view"
```

## Security Considerations

### SSH Key Security

1. **Use dedicated SSH keys** for the MCP server
2. **Protect private keys** with appropriate file permissions:
   ```bash
   chmod 600 ~/.ssh/kubectl_mcp_key
   ```
3. **Use passphrase-protected keys** when possible
4. **Rotate keys regularly** as part of your security policy

### Network Security

1. **Use SSH key authentication** instead of passwords
2. **Limit SSH access** using firewall rules or security groups
3. **Consider using SSH bastion/jump hosts** for additional security
4. **Enable SSH connection logging** on the remote host
5. **Use VPN or private networks** when possible

### Kubernetes Security

1. **Apply RBAC** on the remote cluster to limit what the SSH user can do
2. **Use dedicated service accounts** with minimal required permissions
3. **Audit kubectl operations** on the remote host
4. **Monitor SSH session logs** for unauthorized access

### Current SSH Options

The SSH wrapper uses these options for compatibility:
- `StrictHostKeyChecking=no` - Auto-accepts host keys
- `UserKnownHostsFile=/dev/null` - Doesn't save host keys
- `LogLevel=ERROR` - Reduces verbosity

**Warning:** `StrictHostKeyChecking=no` can expose you to man-in-the-middle attacks. For production use, consider:
1. Manually adding the host key to `~/.ssh/known_hosts` first
2. Modifying the SSH wrapper to use stricter host key checking

## Troubleshooting

### SSH Connection Issues

**Problem:** Connection refused

```bash
# Verify SSH is running on remote host
ssh -v dimtass@192.168.1.130

# Check if the port is correct
ssh -v -p 22 dimtass@192.168.1.130
```

**Problem:** Permission denied

```bash
# Verify SSH key permissions
ls -la ~/.ssh/kubectl_mcp_key  # Should be 600

# Test SSH key authentication
ssh -i ~/.ssh/kubectl_mcp_key -v dimtass@192.168.1.130
```

**Problem:** Host key verification failed

```bash
# Remove old host key
ssh-keygen -R 192.168.1.130

# Or specify known_hosts file
ssh -o UserKnownHostsFile=~/.ssh/known_hosts dimtass@192.168.1.130
```

### Kubectl/Helm Issues

**Problem:** kubectl: command not found

```bash
# Verify kubectl is in remote user's PATH
ssh dimtass@192.168.1.130 'echo $PATH'
ssh dimtass@192.168.1.130 'which kubectl'

# If needed, add to PATH in remote ~/.bashrc or ~/.profile
```

**Problem:** The connection to the server localhost:8080 was refused

```bash
# Verify kubeconfig on remote host
ssh dimtass@192.168.1.130 'kubectl config view'

# Check if kubeconfig exists
ssh dimtass@192.168.1.130 'ls -la ~/.kube/config'
```

**Problem:** Commands timing out

```bash
# Increase timeout if needed (modify natural_language.py)
# Current timeout is 10 seconds

# Or check network connectivity
ssh dimtass@192.168.1.130 'kubectl get nodes'
```

### Debugging

Enable debug logging to see the actual SSH commands being executed:

```bash
# Set Python logging level
export PYTHONLOGLEVEL=DEBUG

# Run the server
python run_server.py
```

The log output will show commands like:
```
DEBUG:kubectl_mcp_tool.utils.ssh_wrapper:Wrapped command: ssh -p 22 -i /Users/user/.ssh/id_rsa -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR dimtass@192.168.1.130 kubectl get pods
```

## Performance Considerations

- **Network latency** will affect command execution time
- **SSH connection overhead** adds to each command
- **Consider persistent SSH connections** for better performance (future enhancement)

## Examples

### Example 1: Basic Pod Listing

With SSH enabled, when you ask the AI assistant:
```
"Show me all pods in the default namespace"
```

The MCP server executes:
```bash
ssh dimtass@192.168.1.130 'kubectl get pods -n default'
```

### Example 2: Helm Chart Installation

When you ask:
```
"Install nginx ingress controller using Helm"
```

The MCP server executes:
```bash
ssh dimtass@192.168.1.130 'helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx'
ssh dimtass@192.168.1.130 'helm repo update'
ssh dimtass@192.168.1.130 'helm install my-nginx ingress-nginx/ingress-nginx -n default'
```

### Example 3: Switching Between Local and Remote

```bash
# Work locally
export KUBECTL_SSH_ENABLED=false
python run_server.py

# Switch to remote
export KUBECTL_SSH_ENABLED=true
export KUBECTL_SSH_USER=dimtass
export KUBECTL_SSH_HOST=192.168.1.130
python run_server.py
```

## Advanced Configuration

### Using SSH Config

You can simplify configuration by using `~/.ssh/config`:

```
Host kubectl-remote
    HostName 192.168.1.130
    User dimtass
    Port 22
    IdentityFile ~/.ssh/kubectl_mcp_key
    StrictHostKeyChecking no
```

Then set:
```bash
export KUBECTL_SSH_ENABLED=true
export KUBECTL_SSH_HOST=kubectl-remote
# User and key will be read from ssh config
```

### Multiple Remote Hosts

To switch between multiple remote hosts, use different environment configurations:

```bash
# Production cluster
export KUBECTL_SSH_ENABLED=true
export KUBECTL_SSH_USER=admin
export KUBECTL_SSH_HOST=k8s-prod.example.com

# Development cluster
export KUBECTL_SSH_ENABLED=true
export KUBECTL_SSH_USER=dev
export KUBECTL_SSH_HOST=k8s-dev.example.com
```

## Future Enhancements

Potential improvements to the SSH functionality:

- [ ] SSH connection pooling/reuse
- [ ] Support for SSH agent forwarding
- [ ] Support for ProxyJump (bastion hosts)
- [ ] Configurable SSH options
- [ ] SSH connection health monitoring
- [ ] Automatic failover to local execution

## Support

For issues or questions:
- GitHub Issues: https://github.com/dimtass/kubectl-mcp-server/issues
- Documentation: See other docs in the `docs/` directory
