# AWS EC2 Deployment Guide - Green AI Video Transcoder

Complete step-by-step guide to deploy your Green AI project to AWS cloud.

---

## Prerequisites

- ✅ AWS account (student account works!)
- ✅ Project working locally with Docker
- ✅ Windows PowerShell (built-in)

---

## PART 1: AWS Console Setup (10 minutes)

### Step 1: Sign In to AWS

1. Go to **https://console.aws.amazon.com/**
2. Sign in with your AWS account credentials
3. **IMPORTANT:** Select region in top-right corner
   - Click region dropdown (e.g., "N. Virginia")
   - Select **"Asia Pacific (Mumbai) ap-south-1"**
   - This is closest to Bangalore = faster speeds

---

### Step 2: Launch EC2 Instance

1. In the **AWS Console search bar** (top), type: `EC2`
2. Click **EC2** (Virtual Servers in the Cloud)
3. Click **"Launch Instance"** button (big orange button)

---

### Step 3: Configure Your Instance

#### **Name and Tags**
- **Name:** `green-ai-transcoder`

#### **Application and OS Images (AMI)**
- Click **"Quick Start"** tab
- Select **Ubuntu**
- Choose **"Ubuntu Server 22.04 LTS (HVM), SSD Volume Type"**
- Architecture: **64-bit (x86)**
- Look for **"Free tier eligible"** badge ✅

#### **Instance Type**
- Select **t2.micro**
- Shows: **1 vCPU, 1 GiB Memory**
- **Free tier eligible** ✅
- Click the checkbox next to it

#### **Key Pair (Login)**
- Click **"Create new key pair"**
- **Key pair name:** `green-ai-key`
- **Key pair type:** RSA
- **Private key file format:** `.pem` (for SSH)
- Click **"Create key pair"** button
- ⚠️ **FILE DOWNLOADS AUTOMATICALLY** to your Downloads folder
- ⚠️ **SAVE THIS FILE!** You need it to access your server

#### **Network Settings**
- Click **"Edit"** button (top right of Network settings section)
- **Firewall (security groups):** Create security group
- **Security group name:** `green-ai-sg`
- **Description:** `Allow SSH and Flask app access`

**Configure Security Group Rules:**

**Rule 1** (SSH - should already be there):
- Type: SSH
- Protocol: TCP
- Port range: 22
- Source type: **My IP** (automatically fills your current IP)
- Description: SSH access

**Rule 2** (Flask App - YOU NEED TO ADD THIS):
- Click **"Add security group rule"** button
- Type: **Custom TCP**
- Protocol: TCP
- Port range: **5000**
- Source type: **Anywhere** (or select "Anywhere IPv4" from dropdown)
- Source: 0.0.0.0/0 (auto-fills)
- Description: `Flask app port`

#### **Configure Storage**
- **Size (GiB):** Change from 8 to **20**
- **Volume type:** gp3 (default)
- **Delete on termination:** Yes (checked)
- Everything else: leave default

#### **Advanced Details**
- Leave everything as default (don't change anything here)

---

### Step 4: Launch Your Instance

1. Review the **Summary** panel (right side):
   - Number of instances: 1
   - Instance type: t2.micro
   - AMI: Ubuntu 22.04 LTS
   
2. Click **"Launch instance"** (orange button, bottom right)

3. You'll see a success page:
   - Click **"View all instances"**

4. **Wait for instance to initialize:**
   - **Instance State:** pending → **running** ✅ (takes 1-2 minutes)
   - **Status check:** Initializing → **2/2 checks passed** ✅ (takes 2-3 minutes)
   - Refresh the page if needed

---

### Step 5: Note Your Instance Details

1. Click on your instance (click the row or checkbox)
2. In the **Details** tab (bottom panel), find and **WRITE DOWN**:
   - **Instance ID:** `i-0123456789abcdef`
   - **Public IPv4 address:** `XX.XXX.XXX.XXX` ← **YOU NEED THIS!**
   - **Public IPv4 DNS:** `ec2-xx-xxx-xxx-xxx.ap-south-1.compute.amazonaws.com`

**Write your Public IP here:** `___.___.___.___`

---

## PART 2: Connect to Your EC2 Instance (5 minutes)

### Step 6: Prepare Your SSH Key

Open **PowerShell** on your Windows laptop:

```powershell
# Create .ssh directory if it doesn't exist
mkdir C:\Users\saran\.ssh -ErrorAction SilentlyContinue

# Move the downloaded key from Downloads to .ssh folder
Move-Item C:\Users\saran\Downloads\green-ai-key.pem C:\Users\saran\.ssh\green-ai-key.pem -Force

# Fix file permissions (REQUIRED for SSH to work)
icacls C:\Users\saran\.ssh\green-ai-key.pem /inheritance:r
icacls C:\Users\saran\.ssh\green-ai-key.pem /grant:r "$($env:USERNAME):(R)"
```

**Expected output:**
```
processed file: C:\Users\saran\.ssh\green-ai-key.pem
Successfully processed 1 files; Failed processing 0 files
```

---

### Step 7: SSH Into Your EC2 Instance

```powershell
# Replace XX.XXX.XXX.XXX with YOUR instance's Public IPv4 address
ssh -i C:\Users\saran\.ssh\green-ai-key.pem ubuntu@3.110.171.248
```

**First time connecting, you'll see:**
```
The authenticity of host 'XX.XXX.XXX.XXX (XX.XXX.XXX.XXX)' can't be established.
ECDSA key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

**Type:** `yes` and press **Enter**

**You should now see:**
```
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-1051-aws x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

ubuntu@ip-172-31-XX-XXX:~$ 
```

✅ **SUCCESS! You're now inside your AWS server!**

---

## PART 3: Install Docker on EC2 (10 minutes)

**All commands below are typed in the EC2 SSH session**

### Step 8: Update System Packages

```bash
# Update package list
sudo apt update
```

**Takes 30-60 seconds**

You'll see:
```
Hit:1 http://ap-south-1.ec2.archive.ubuntu.com/ubuntu jammy InRelease
...
Reading package lists... Done
```

---

### Step 9: Install Docker

```bash
# Install Docker
sudo apt install -y docker.io
```

**Takes 2-3 minutes**

You'll see lots of package installation output.

---

### Step 10: Install Docker Compose

```bash
# Install Docker Compose
sudo apt install -y docker-compose
```

**Takes 1-2 minutes**

---

### Step 11: Configure Docker

```bash
# Start Docker service
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Add ubuntu user to docker group (so you don't need sudo)
sudo usermod -aG docker ubuntu
```

**Expected output:**
```
Synchronizing state of docker.service with SysV service script...
Created symlink /etc/systemd/system/multi-user.target.wants/docker.service...
```

---

### Step 12: Re-login for Group Changes

**IMPORTANT:** You must logout and login again for docker group to work

```bash
exit
```

**Then SSH back in:**
```powershell
ssh -i C:\Users\saran\.ssh\green-ai-key.pem ubuntu@3.110.163.52
```

---

### Step 13: Verify Docker Installation

```bash
# Check Docker version
docker --version
```

**Should show:**
```
Docker version 24.0.5, build 24.0.5-0ubuntu1~22.04.1
```

```bash
# Check Docker Compose version
docker-compose --version
```

**Should show:**
```
docker-compose version 1.29.2, build unknown
```

✅ **Docker is ready!**

---

## PART 4: Upload Your Project to EC2 (5 minutes)

### Step 14: Transfer Files Using SCP

**Open a NEW PowerShell window on your laptop** (keep the SSH session open in another window)

```powershell
# Navigate to your project directory
cd C:\Users\saran\Downloads\badal

# Verify you're in the right place
ls
```

**You should see:**
```
backend/
frontend/
Dockerfile
docker-compose.yml
README.md
...
```

**Upload entire project to EC2:**
```powershell
# Replace XX.XXX.XXX.XXX with your EC2 Public IPv4 address
scp -i C:\Users\saran\.ssh\green-ai-key.pem -r . ubuntu@65.2.122.97:~/badal
```

**This uploads all files** (takes 1-2 minutes)

You'll see:
```
Dockerfile                      100%  665    15.2KB/s   00:00
docker-compose.yml              100%  312     7.1KB/s   00:00
app.py                          100% 8432   192.5KB/s   00:00
...
```

✅ **Files uploaded!**

---

## PART 5: Build and Run Your App (15 minutes)

### Step 15: Verify Files on EC2

**Back in your EC2 SSH session:**

```bash
# Navigate to project folder
cd ~/badal

# List files
ls -la
```

**You should see:**
```
drwxr-xr-x  6 ubuntu ubuntu  4096 Oct 28 10:30 .
drwxr-xr-x  3 ubuntu ubuntu  4096 Oct 28 10:29 ..
drwxr-xr-x  2 ubuntu ubuntu  4096 Oct 28 10:30 backend
drwxr-xr-x  2 ubuntu ubuntu  4096 Oct 28 10:30 frontend
-rw-r--r--  1 ubuntu ubuntu   665 Oct 28 10:30 Dockerfile
-rw-r--r--  1 ubuntu ubuntu   312 Oct 28 10:30 docker-compose.yml
...
```

✅ **All files are there!**

---

### Step 16: Build Docker Image

```bash
# Build the Docker image
docker-compose build
```

**⏰ This takes 5-10 minutes** (FFmpeg installation is slow)

You'll see output like:
```
[+] Building 300.5s (15/15) FINISHED
=> [internal] load build definition from Dockerfile
=> => transferring dockerfile: 665B
=> [internal] load .dockerignore
=> [1/8] FROM docker.io/library/python:3.11-slim
=> [2/8] RUN apt-get update && apt-get install -y ffmpeg libgl1...
=> [3/8] WORKDIR /app
=> [4/8] COPY backend/requirements.txt ./backend/
=> [5/8] RUN pip install --no-cache-dir -r backend/requirements.txt
=> [6/8] COPY backend/ ./backend/
=> [7/8] COPY frontend/ ./frontend/
=> [8/8] RUN mkdir -p uploads outputs
=> exporting to image
=> => naming to docker.io/library/badal-web
```

☕ **Grab a coffee! First build is slow.**

---

### Step 17: Start Your Application

```bash
# Start container in background mode
docker-compose up -d
```

**Takes 5-10 seconds**

**Expected output:**
```
[+] Running 2/2
 ✔ Network badal_default  Created
 ✔ Container badal-web-1  Started
```

---

### Step 18: Verify Container is Running

```bash
# Check container status
docker-compose ps
```

**Should show:**
```
NAME          IMAGE       COMMAND                  SERVICE   CREATED         STATUS         PORTS
badal-web-1   badal-web   "python backend/app.py"  web       30 seconds ago  Up 28 seconds  0.0.0.0:5000->5000/tcp
```

**Check application logs:**
```bash
docker-compose logs
```

**Should show:**
```
badal-web-1  |  * Serving Flask app 'app'
badal-web-1  |  * Debug mode: off
badal-web-1  | WARNING: This is a development server...
badal-web-1  |  * Running on all addresses (0.0.0.0)
badal-web-1  |  * Running on http://127.0.0.1:5000
badal-web-1  |  * Running on http://172.18.0.2:5000
badal-web-1  | Press CTRL+C to quit
```

✅ **APP IS RUNNING!**

---

## PART 6: Access Your Application (2 minutes)

### Step 19: Open in Browser

**On your laptop, open any web browser:**

```
http://65.2.122.97:5000
```

**Replace `XX.XXX.XXX.XXX` with your EC2 Public IPv4 address**

**Example:** If your IP is `13.127.45.89`, go to:
```
http://13.127.45.89:5000
```

**YOU SHOULD SEE YOUR GREEN AI VIDEO TRANSCODER!** 🎉

---

## PART 7: Test Your Deployment (5 minutes)

### Step 20: Upload a Test Video

1. Click **"Choose File"** button
2. Select a short video (5-15 seconds recommended)
3. Click **"Upload and Transcode"** button
4. Wait for processing (you'll see a loading indicator)

---

### Step 21: Monitor Logs in Real-Time

**In your EC2 SSH session:**

```bash
# Follow logs live
docker-compose logs -f
```

**You'll see:**
```
web-1  | 172.18.0.1 - - [28/Oct/2025 10:45:12] "POST /upload HTTP/1.1" 200 -
web-1  | Analyzing video complexity...
web-1  | Debug - Edge: 0.0234 (3.51/10), Motion: 0.0127 (3.17/10)
web-1  | Complexity score: 5.04/10
web-1  | Green AI: Using preset=superfast, crf=23 for complexity=5.04
web-1  | normal mode: duration=12.5s, baseline_cpu=5.2%, avg_cpu=52.1%, energy=182.35J, samples=62
web-1  | green mode: duration=8.7s, baseline_cpu=5.3%, avg_cpu=41.5%, energy=101.29J, samples=43
web-1  | ✅ Results saved successfully to outputs/results.xlsx
```

**Press `Ctrl+C` to exit log view (app keeps running)**

**Notice:** `baseline_cpu` is ~5% on EC2 vs ~15-25% on your laptop! ✅

---

### Step 22: View Results

**Back in your browser:**
- You should see the results page with:
  - Complexity score
  - Normal mode energy and time
  - Green AI mode energy and time
  - Energy savings percentage
  - Two video players (normal vs green)

✅ **IT WORKS!**

---

## Common Commands Reference

### Viewing Logs

```bash
# Follow logs in real-time (Ctrl+C to exit)
docker-compose logs -f

# View last 50 lines
docker-compose logs --tail 50

# View logs for specific service
docker-compose logs web
```

### Managing the Application

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Rebuild and restart after code changes
docker-compose down
docker-compose build
docker-compose up -d
```

### Checking Status

```bash
# Check container status
docker-compose ps

# Check Docker status
docker ps

# Check system resources
docker stats

# Check disk space
df -h
```

### Cleaning Up

```bash
# Remove old videos
rm ~/badal/uploads/*
rm ~/badal/outputs/*

# Clean Docker cache (if running out of space)
docker system prune -a

# View disk usage
du -sh ~/badal/*
```

---

## Updating Your Code

**If you make changes locally and want to update EC2:**

### Step 1: Upload Changed Files

**On your laptop (PowerShell):**

```powershell
cd C:\Users\saran\Downloads\badal

# Upload only backend changes
scp -i C:\Users\saran\.ssh\green-ai-key.pem -r backend ubuntu@3.110.115.248:~/badal/

# Or upload frontend changes
scp -i C:\Users\saran\.ssh\green-ai-key.pem -r frontend ubuntu@XX.XXX.XXX.XXX:~/badal/

# Or upload everything
scp -i C:\Users\saran\.ssh\green-ai-key.pem -r . ubuntu@3.110.163.52:~/badal/
```

### Step 2: Rebuild on EC2

**In your EC2 SSH session:**

```bash
cd ~/badal

# Stop current container
docker-compose down

# Rebuild image with new code
docker-compose build

# Start updated container
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## Troubleshooting

### Can't Access Port 5000 in Browser

**Check Security Group:**
1. AWS Console → EC2 → Security Groups
2. Find `green-ai-sg`
3. Click "Inbound rules" tab
4. Verify you have:
   - Type: Custom TCP, Port: 5000, Source: 0.0.0.0/0

**If missing, add it:**
1. Click "Edit inbound rules"
2. Click "Add rule"
3. Type: Custom TCP, Port: 5000, Source: Anywhere (0.0.0.0/0)
4. Click "Save rules"

---

### Container Not Running

```bash
# Check status
docker-compose ps

# If stopped, check logs for errors
docker-compose logs

# Common issue: Port already in use
# Solution: Stop and restart
docker-compose down
docker-compose up -d
```

---

### Out of Disk Space

```bash
# Check disk usage
df -h

# If /dev/xvda1 is >90% full:
# Clean old videos
rm ~/badal/uploads/*
rm ~/badal/outputs/*

# Clean Docker cache
docker system prune -a

# Rebuild
docker-compose build
```

---

### SSH Connection Refused

**Your IP might have changed:**

1. Find your current IP: Google "what is my ip"
2. AWS Console → EC2 → Security Groups → green-ai-sg
3. Edit inbound rules → SSH rule → Source → **My IP**
4. Save rules
5. Try SSH again

---

### Build Fails

```bash
# Check available space
df -h

# If low, clean up
docker system prune -a

# Try building again
docker-compose build --no-cache
```

---

## Optional: Allocate Elastic IP (Fixed IP Address)

**Problem:** EC2 public IP changes when you stop/start instance

**Solution:** Allocate an Elastic IP (free while instance is running)

### Steps:

1. **AWS Console → EC2 → Elastic IPs** (left sidebar)
2. Click **"Allocate Elastic IP address"**
3. Click **"Allocate"**
4. Select the new Elastic IP
5. **Actions** → **Associate Elastic IP address**
6. **Instance:** Select `green-ai-transcoder`
7. Click **"Associate"**

**Now your IP won't change!** Update your bookmarks with the new Elastic IP.

---

## Cost Management

### Free Tier Limits (12 months from signup)

- **EC2 t2.micro:** 750 hours/month (= 24/7 for 1 instance) ✅
- **EBS Storage:** 30 GB ✅
- **Data Transfer:** 100 GB/month outbound ✅

**Your current usage:**
- ✅ 1 t2.micro running 24/7: **FREE**
- ✅ 20 GB storage: **FREE**
- ✅ Likely under 100 GB transfer: **FREE**

**Estimated monthly cost: $0** (within free tier)

---

### Stopping Your Instance to Save Costs

**If you're done for the day:**

```bash
# In EC2 SSH session
docker-compose down
exit
```

**AWS Console:**
1. EC2 → Instances
2. Select your instance
3. Instance State → **Stop instance**

**Note:** You still pay for EBS storage (~$2/month for 20GB)

**To restart later:**
1. Instance State → **Start instance**
2. Wait for new Public IP (or use Elastic IP)
3. SSH back in
4. `cd ~/badal && docker-compose up -d`

---

### Terminating Your Instance (Permanent Delete)

**⚠️ WARNING: This deletes everything!**

**Backup first:**
```bash
# Download results Excel file
scp -i C:\Users\saran\.ssh\green-ai-key.pem ubuntu@XX.XXX.XXX.XXX:~/badal/outputs/results.xlsx ./
```

**Then terminate:**
1. AWS Console → EC2 → Instances
2. Select instance
3. Instance State → **Terminate instance**
4. Confirm

**All data lost, no charges after termination.**

---

## Success Checklist

- ✅ AWS account created
- ✅ EC2 instance launched (t2.micro, Ubuntu 22.04)
- ✅ Security group configured (SSH port 22, Flask port 5000)
- ✅ SSH key downloaded and configured
- ✅ Successfully connected via SSH
- ✅ Docker and Docker Compose installed
- ✅ Project files uploaded to EC2
- ✅ Docker image built successfully
- ✅ Container running
- ✅ Application accessible at http://YOUR-IP:5000
- ✅ Video upload and transcoding working
- ✅ Energy measurements showing cleaner baseline (~5% vs laptop's ~20%)
- ✅ Results displayed correctly
- ✅ Can view logs and monitor application

---

## What You Can Now Say in Your Case Study

✅ **"Deployed containerized application to AWS EC2 cloud infrastructure"**  
✅ **"Utilized cloud computing for scalable video processing"**  
✅ **"Achieved more accurate energy measurements in dedicated cloud environment"**  
✅ **"Demonstrated DevOps skills: Docker containerization, AWS deployment, cloud management"**  
✅ **"Application publicly accessible for demonstration and testing"**  
✅ **"Implemented production-ready deployment with persistent storage and logging"**

---

## Your Public Demo URL

```
http://XX.XXX.XXX.XXX:5000
```

**Share this with:**
- Your teacher (for grading)
- Classmates (for demo)
- Put in presentation slides
- Add to resume/portfolio
- Include in project documentation

---

## Next Steps

Now that your app is deployed to AWS:

1. **Test with multiple videos** - verify consistency
2. **Monitor energy measurements** - should be cleaner than laptop
3. **Collect training data** - for ML model (future enhancement)
4. **Document everything** - screenshots, metrics, results
5. **Prepare presentation** - show live demo from AWS

---

## Need Help?

**Check logs first:**
```bash
docker-compose logs -f
```

**Common issues:**
- Can't access in browser → Check security group port 5000
- Container won't start → Check logs for errors
- Out of space → Clean old videos and Docker cache
- SSH doesn't work → Check security group allows your IP

**Still stuck?** Check AWS documentation or ask your teacher!

---

## 🎉 Congratulations!

**Your Green AI Video Transcoder is now live in the cloud!**

You've successfully:
- Deployed to AWS cloud infrastructure
- Containerized a full-stack application
- Set up production-ready environment
- Created a publicly accessible demo

**This is impressive portfolio material!** 🚀

---

**Made with ❤️ for your case study project**
**Good luck with your presentation!** 🎓
