## Requirements

### Operating system
- Linux or macOS

### Python
- Python **3.9 or newer**

### Python dependencies
Install required Python package:

```bash
pip install waldur-api-client
```

### System dependencies (mandatory)

The script relies on SSH key generation, SSH connectivity checks, and mounting the HPC home directory using SSHFS.

#### Common
The following tools must be available in `PATH`:
- `ssh`
- `ssh-keygen`
- `sshfs`

#### Linux
Install `sshfs` using your distribution package manager:

```bash
# RHEL / CentOS / Alma / Rocky
yum install sshfs

# Debian / Ubuntu
apt-get install sshfs
```

#### macOS
Install FUSE and SSHFS using Homebrew:

```bash
brew install --cask macfuse
brew install gromgit/fuse/sshfs-mac
```

> Note: On macOS, macFUSE requires approval in  
> **System Settings → Privacy & Security** after installation.

---

## How to run

### Option 1: From Terminal

1. Clone the repository:
   ```bash
   git clone https://github.com/rtuhpc/configureHPC.git
   cd configureHPC
   ```

2. Ensure `config.ini` is configured correctly.

3. Run the script:
   ```bash
   python3 configure_HPC_v1.1.py
   ```

4. When prompted, paste your **Waldur API token**.

### Option 2: Using the Desktop Shortcut (Linux)

A pre-configured `.desktop` file is included for Linux systems.

- Save it to your Desktop and make it executable:
  ```bash
  chmod +x ~/Desktop/Configure\ HPC.desktop
  ```
- Double-click to run the script in a terminal window.
- The `sleep 120` ensures the terminal remains open after execution so you can read messages.

---
