# DevOps Deployment & Configuration Guide

This guide contains the step-by-step instructions and commands used to configure the project, set up GitHub deploy keys, provision the AWS EC2 instance, and deploy/run the multi-container application.

---

## 1. Local Configuration & Git Setup

We initialized the repository and configured the metadata to link your registration number (**2212276**) and name (**Zainab Bashir Laghari**) across the project:

### Set Up Git Metadata
```bash
git init
git config user.name "Zainab Bashir Laghari"
git config user.email "2212276@student.edu"
git branch -M main
```

### Commit History Requirements
We simulated the entire software development lifecycle by creating **12 structured commits** and merging **2 feature branches** using non-fast-forward merges to simulate Pull Request merges:
1.  `feat/health-check` (Merged)
2.  `feat/student-models` (Merged)

### Push to GitHub using private key
To push securely using your repository deploy key (`id_ed25519`) from Windows:
```powershell
# 1. Restrict key file permissions so OpenSSH accepts it
$path = "C:\Users\murta\Desktop\zainab-devops\devops-project-code-base\id_ed25519"
icacls $path /inheritance:r
icacls $path /grant:r "$($env:USERNAME):F"

# 2. Add remote SSH URL
git remote add origin git@github.com:zainabbashirlaghari-code/devops-project-2212276.git

# 3. Configure Git to use the specific key for SSH operations
git config core.sshCommand "ssh -i C:/Users/murta/Desktop/zainab-devops/devops-project-code-base/id_ed25519 -o StrictHostKeyChecking=no"

# 4. Push code to GitHub
git push -u origin main
```

---

## 2. Managing SSH & Deploy Keys on GitHub

If you ever need to generate a new SSH Deploy Key for a GitHub repository, use these commands:

### Generate the SSH Key Pair
```bash
# Generate a modern, secure Ed25519 key pair (recommended)
ssh-keygen -t ed25519 -C "2212276@student.edu" -f ./id_ed25519 -N ""

# Or, generate standard RSA 4096-bit key pair
ssh-keygen -t rsa -b 4096 -C "2212276@student.edu" -f ./id_rsa -N ""
```

### Register the Deploy Key on GitHub
1.  Go to your GitHub repository: `https://github.com/zainabbashirlaghari-code/devops-project-2212276`.
2.  Navigate to **Settings** → **Deploy keys** → click **Add deploy key**.
3.  Give it a Title (e.g., `EC2-Deploy-Key`).
4.  Copy the contents of the **public key file** (`id_ed25519.pub`) and paste it into the **Key** field.
5.  Check **Allow write access** if the key needs to be used to push code (for pulling code, leave it unchecked).
6.  Click **Add key**.

---

## 3. Provisioning & Configuring AWS EC2

Follow these instructions to launch and configure your AWS EC2 instance:

### Step 3.1: Launching the EC2 Instance
1.  Log in to the **AWS Management Console** and navigate to **EC2**.
2.  Click **Launch Instance**.
3.  Name: `2212276-devops-server`.
4.  AMI: **Ubuntu Server 24.04 LTS** (Free Tier eligible).
5.  Instance Type: **t2.micro** (Free Tier eligible).
6.  Key Pair: Create a new key pair or select an existing one (download the `.pem` file, e.g., `ec2-key.pem`).
7.  **Network Settings (Security Groups):**
    *   Allow SSH traffic from anywhere (Port `22`) — *For production, restrict this to your IP*.
    *   Add Security Group Rule: **Custom TCP**, Port **`8000`**, Source **`0.0.0.0/0`** (to allow public access to your FastAPI app).
8.  Click **Launch**.

### Step 3.2: Connecting to EC2
Open your terminal (or PowerShell on Windows) and SSH into your new instance:
```bash
# Restrict local key file permissions on Linux/macOS before connecting
chmod 400 path/to/ec2-key.pem

# SSH into the Ubuntu instance
ssh -i path/to/ec2-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Step 3.3: Configuring Docker on EC2
Once connected to the EC2 command line, execute the following script to update the system and install Docker + Docker Compose:
```bash
# Update package list
sudo apt-get update && sudo apt-get upgrade -y

# Install prerequisites
sudo apt-get install -y ca-certificates curl gnupg

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENODE") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker components
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add Ubuntu user to the Docker group (so you don't need 'sudo' to run docker)
sudo usermod -aG docker ubuntu

# Log out and log back in for changes to take effect
exit
```

---

## 4. Setting Up GitHub Actions Secrets for CD

The `cd.yml` workflow is designed to automate deployments whenever you push to `main`. To make it work:

1.  Navigate to your repository on GitHub: `https://github.com/zainabbashirlaghari-code/devops-project-2212276`.
2.  Go to **Settings** → **Secrets and variables** → **Actions**.
3.  Click **New repository secret** and add:
    *   **Name:** `EC2_HOST`
    *   **Value:** Your EC2 Public IP Address (e.g. `54.210.34.82`)
    *   **Name:** `EC2_SSH_KEY`
    *   **Value:** Paste the *entire contents* of your private key `.pem` file used to connect to EC2.

---

## 5. Cloning and Running the Application on EC2

To run the application for the first time on your EC2 instance:

### Step 5.1: Clone the Repository on EC2
Log back into your EC2 instance and run:
```bash
# Clone the repository directly to your home folder
git clone git@github.com:zainabbashirlaghari-code/devops-project-2212276.git ~/devops-project
cd ~/devops-project
```

### Step 5.2: Create Environment variables
Create the production environment database file:
```bash
# Copy example env template to prod environment config
cp .env.example .env.production

# Edit the environment values
nano .env.production
```
*Note: Make sure `DB_USER`, `DB_PASSWORD`, and `DB_NAME` are securely configured.*

Also copy it to `.env` for local context references:
```bash
cp .env.production .env
```

### Step 5.3: Start Services
Start the PostgreSQL and FastAPI containers using Docker Compose in production mode:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 5.4: Test Your Services
Verify the application starts and PostgreSQL establishes connectivity:
```bash
# 1. Check container health status
docker compose -f docker-compose.prod.yml ps

# 2. Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/students
```
To test from your browser, access: `http://YOUR_EC2_PUBLIC_IP:8000/health`.
