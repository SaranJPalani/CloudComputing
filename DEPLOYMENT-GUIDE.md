# 🚀 Green AI Video Transcoder - Deployment Guide

## 📋 Table of Contents
1. [Docker Commands](#docker-commands)
2. [Kubernetes Deployment](#kubernetes-deployment)
3. [Testing & Monitoring](#testing--monitoring)
4. [Troubleshooting](#troubleshooting)

---

## 🐳 Docker Commands

### Building the Docker Image

```powershell
docker-compose build
```
**What it does:** 
- Reads `Dockerfile` and `docker-compose.yml`
- Creates a Docker image with Python 3.11, FFmpeg, OpenCV
- Installs all dependencies from `requirements.txt`
- Packages your Flask backend and frontend into a container
- Tags the image as `badal-web:latest`

**Use the `--no-cache` flag for clean rebuilds:**
```powershell
docker-compose build --no-cache
```
This forces Docker to rebuild everything from scratch (useful after code changes).

---

### Running the Container

```powershell
docker-compose up
```
**What it does:**
- Starts the container from the `badal-web` image
- Maps port 5000 (container) to port 5000 (your PC)
- Mounts `./uploads` and `./outputs` folders for persistent storage
- Starts Flask server at http://localhost:5000
- Shows live logs in terminal (press Ctrl+C to stop)

**Run in background (detached mode):**
```powershell
docker-compose up -d
```
Container runs in background. View logs with `docker-compose logs`.

---

### Stopping the Container

```powershell
docker-compose down
```
**What it does:**
- Stops the running container
- Removes the container (but keeps the image)
- Keeps your data in `uploads/` and `outputs/` folders

---

### Viewing Logs

```powershell
docker-compose logs
```
**What it does:**
- Shows all output from the Flask app
- Includes debug prints, errors, HTTP requests
- Useful for troubleshooting

**Follow logs in real-time:**
```powershell
docker-compose logs -f
```

---

### Managing Docker Images

**List all images:**
```powershell
docker images
```

**Remove old images:**
```powershell
docker rmi badal-web:latest -f
```
The `-f` flag forces removal even if containers exist.

**Remove ALL unused images/containers (clean slate):**
```powershell
docker system prune -a
```
⚠️ Warning: This deletes everything not currently running!

---

## ☸️ Kubernetes Deployment

### Prerequisites Check

**1. Verify Kubernetes is installed:**
```powershell
kubectl version --client
```
**What it does:** Shows Kubernetes CLI version. If you see version info, you're ready!

**Expected output:**
```
Client Version: v1.32.2
Kustomize Version: v5.5.0
```

**2. Enable Kubernetes in Docker Desktop:**
- Open Docker Desktop
- Go to Settings → Kubernetes
- Check "Enable Kubernetes"
- Click "Apply & Restart"
- Wait for the green indicator (may take 2-3 minutes)

---

### Step 1: Deploy with YAML (Includes Volume Mappings!)

**⚠️ IMPORTANT:** Use the YAML file to get persistent storage! Videos will save to your local folders.

```powershell
kubectl apply -f k8s-deployment.yaml
```

**What it does:**
- Creates **Deployment** with 3 replicas using `badal-web:latest` image
- Creates **Service** (LoadBalancer) exposing port 80
- **Maps volumes** so uploads/outputs save to `C:\Users\saran\Downloads\badal\`
- All in ONE command!

**Alternative (CLI-only, NO volume mappings):**

⚠️ **Warning:** This method does NOT save videos to your folders. They'll be lost when pods restart!

```powershell
# Create deployment
kubectl create deployment green-video --image=badal-web:latest --replicas=3 --port=5000

# Expose service
kubectl expose deployment green-video --type=LoadBalancer --port=80 --target-port=5000
```

**Why use YAML?**
- ✅ Videos saved to your local `uploads/` and `outputs/` folders
- ✅ Excel results persist across pod restarts
- ✅ All users' uploads visible on your PC
- ❌ CLI method can't add volumes after deployment creation

---

### Step 2: Verify Deployment

**Check pods are running:**
```powershell
kubectl get pods
```

**Expected output:**
```
NAME                           READY   STATUS    RESTARTS   AGE
green-video-78888bc4d7-cqj92   1/1     Running   0          2m
green-video-78888bc4d7-hhz6h   1/1     Running   0          2m
green-video-78888bc4d7-vjfpx   1/1     Running   0          2m
```

**Check service URL:**
```powershell
kubectl get service green-video
```

**Expected output:**
```
NAME          TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
green-video   LoadBalancer   10.101.139.38   localhost     80:30788/TCP   5m
```

**Access your app at:** `http://localhost`

---

### Step 3: Update to Latest Version (After Code Changes)

**After rebuilding Docker image with fixes:**

```powershell
# Delete old deployment
kubectl delete deployment green-video

# Reapply with new image
kubectl apply -f k8s-deployment.yaml
```

**What it does:**
- Removes old pods with outdated code
- Creates new pods with latest Docker image (`badal-web:latest`)
- Service remains running (no need to recreate)
- Zero downtime if you use rolling update (see advanced section)

**Quick check:**
```powershell
kubectl get pods
```
Watch for STATUS changing from `ContainerCreating` → `Running`

---

## 🌐 Sharing with Others (ngrok)

**Start ngrok tunnel:**
```powershell
ngrok http 80
```

**What it does:**
- Creates public URL like `https://abc123.ngrok-free.app`
- Tunnels traffic to your Kubernetes service on port 80
- Anyone can access your app from anywhere!
- Load balances across all 3 K8s pods automatically

**Share the ngrok URL** with friends/testers. They upload videos → videos save to your `C:\Users\saran\Downloads\badal\uploads\` folder! 🎉

---

## 🧪 Testing & Monitoring

### Testing Load Balancing

Upload videos at http://localhost and watch logs from different pods handling requests:

```powershell
kubectl logs -f deployment/green-video
```

**What it does:**
- Streams logs from ALL pods in the deployment
- You'll see different pods processing different videos
- Demonstrates load distribution

---

### Manual Scaling

**Scale UP to 5 replicas:**
```powershell
kubectl scale deployment green-video --replicas=5
```

**What it does:**
- Increases pods from 3 to 5
- Kubernetes automatically creates 2 more pods
- More capacity for concurrent video processing

**Scale DOWN to 2 replicas:**
```powershell
kubectl scale deployment green-video --replicas=2
```

**What it does:**
- Decreases pods from current count to 2
- Kubernetes gracefully terminates excess pods
- Saves resources when load is low

---

### Auto-Scaling (Advanced)

```powershell
kubectl autoscale deployment green-video --cpu-percent=70 --min=2 --max=10
```

**What it does:**
- Creates a **Horizontal Pod Autoscaler (HPA)**
- If CPU usage > 70%, Kubernetes adds more pods
- Minimum: 2 pods (even if idle)
- Maximum: 10 pods (prevents runaway scaling)
- Automatically scales based on demand!

**Check autoscaler status:**
```powershell
kubectl get hpa
```

---

### Demonstrating Self-Healing

**Delete a pod manually:**
```powershell
kubectl get pods
# Copy one pod name, e.g., green-video-6d4f8b9c7-abc12
kubectl delete pod green-video-6d4f8b9c7-abc12
```

**What happens:**
- Kubernetes immediately detects the missing pod
- Automatically creates a new pod to maintain 3 replicas
- Zero downtime! Other pods continue serving traffic

**Watch it happen in real-time:**
```powershell
kubectl get pods --watch
```
Press Ctrl+C to stop watching.

---

### Rolling Updates (Zero-Downtime Deployment)

**Scenario:** You made code changes and rebuilt the image as v2.

```powershell
# Build new version
docker-compose build
docker tag badal-web:latest badal-web:v2

# Update deployment
kubectl set image deployment/green-video green-video=badal-web:v2
```

**What it does:**
- Gradually replaces old pods with new ones
- Kubernetes ensures at least 2 pods are always running
- Users experience zero downtime
- Old pods only terminate after new ones are healthy

**Watch the rollout:**
```powershell
kubectl rollout status deployment/green-video
```

**Rollback if something breaks:**
```powershell
kubectl rollout undo deployment/green-video
```

---

### Concurrent Video Processing Test

**Upload 3 videos simultaneously** (open 3 browser tabs at http://localhost):
- Tab 1: Upload video_1.mp4
- Tab 2: Upload video_2.mp4  
- Tab 3: Upload video_3.mp4

**What happens:**
- Each request goes to a different pod (load balancing)
- All 3 videos process **at the same time**
- Check logs to see which pod handled which video

---

## 📊 Monitoring Commands

### View Pod Details
```powershell
kubectl describe pod <pod-name>
```
Shows detailed info: IP, node, events, resource usage.

### View Pod Logs
```powershell
kubectl logs <pod-name>
```
Shows logs from a specific pod (useful for debugging).

### Resource Usage
```powershell
kubectl top pods
```
Shows CPU and memory usage per pod (requires metrics-server).

### Port Forwarding (Alternative Access)
```powershell
kubectl port-forward deployment/green-video 8080:5000
```
Access at http://localhost:8080 (bypasses LoadBalancer).

---

## 🛑 Cleanup Commands

### Delete the Service (Stop External Access)
```powershell
kubectl delete service green-video
```
Pods keep running but are no longer accessible from outside.

### Delete the Deployment (Remove All Pods)
```powershell
kubectl delete deployment green-video
```
Stops and removes all pods. Your Docker image remains.

### Delete Everything at Once
```powershell
kubectl delete deployment green-video
kubectl delete service green-video
```

---

## 🐛 Troubleshooting

### Pods Not Starting?

**Check pod status:**
```powershell
kubectl get pods
kubectl describe pod <pod-name>
```

**Common issues:**
- `ImagePullBackOff`: Image not found locally. Rebuild with `docker-compose build`.
- `CrashLoopBackOff`: Container crashes immediately. Check logs with `kubectl logs <pod-name>`.
- `Pending`: Insufficient resources. Try scaling down or restarting Docker Desktop.

---

### Service Not Accessible?

**Verify service exists:**
```powershell
kubectl get service green-video
```

**Check EXTERNAL-IP:**
- Should show `localhost` on Docker Desktop
- If `<pending>`, wait 30 seconds and check again
- If stuck, delete and recreate service

---

### Image Not Found?

**Kubernetes can't find `badal-web:latest`:**

Solution: Kubernetes uses Docker Desktop's local images. Ensure you built the image:
```powershell
docker images | findstr badal
```
You should see `badal-web` with tag `latest`.

If missing, rebuild:
```powershell
docker-compose build
```

---

### Videos Not Processing?

**Check pod logs:**
```powershell
kubectl logs -f deployment/green-video
```

Look for errors like:
- `FFmpeg not found`: Image build failed. Rebuild with `docker-compose build --no-cache`.
- `Permission denied`: Volume mounting issue. Not applicable with Docker Desktop K8s (uses local image).

---

## 📝 Quick Reference

### Docker Workflow
1. `docker-compose build` → Build image
2. `docker-compose up` → Run container
3. Test at http://localhost:5000
4. `docker-compose down` → Stop container

### Kubernetes Workflow (YAML Method - Recommended)
1. `kubectl apply -f k8s-deployment.yaml` → Deploy with volume mappings
2. `kubectl get pods` → Verify 3 pods running
3. `kubectl get service green-video` → Get access URL
4. Test at http://localhost
5. `ngrok http 80` → Share publicly
6. **Update after code changes:** `kubectl delete deployment green-video` + `kubectl apply -f k8s-deployment.yaml`
7. **Cleanup:** `kubectl delete -f k8s-deployment.yaml`

### Kubernetes Workflow (CLI Method - No Volumes)
⚠️ **Warning:** Videos won't save to your local folders with this method!

1. `kubectl create deployment green-video --image=badal-web:latest --replicas=3 --port=5000`
2. `kubectl expose deployment green-video --type=LoadBalancer --port=80 --target-port=5000`
3. `kubectl get service green-video` → Get URL
4. Test at http://localhost
5. `kubectl delete deployment green-video` + `kubectl delete service green-video` → Cleanup

---

## 🎯 Case Study Demonstrations

### 1. Container Images (Docker)
- Show `Dockerfile` with multi-stage comments
- Explain `docker-compose.yml` volume mappings
- Demonstrate `docker-compose build --no-cache`
- Show image layers with `docker history badal-web`

### 2. Kubernetes Operations
- Deploy with 3 replicas (high availability)
- Scale up/down manually (elasticity)
- Auto-scaling with HPA (automation)
- Self-healing by deleting a pod (resilience)
- Rolling update with zero downtime (continuous delivery)
- Concurrent processing demo (parallelism)

### 3. Green AI
- Show CARBON_INTENSITY = 710 in `backend/app.py`
- Cite BESCOM 2023-24 data (0.71 tCO2/MWh)
- Demonstrate complexity analysis (low/medium/high videos)
- Compare energy/CO2 between normal and Green AI modes
- Show `outputs/results.xlsx` with savings data

---

## 💡 Pro Tips

1. **Always check pod status** before assuming failure:
   ```powershell
   kubectl get pods
   ```

2. **Use `--watch` to monitor changes** in real-time:
   ```powershell
   kubectl get pods --watch
   ```

3. **Logs are your best friend** for debugging:
   ```powershell
   kubectl logs -f deployment/green-video
   ```

4. **Test locally with Docker first** before K8s:
   - Easier to debug
   - Faster iteration
   - K8s adds complexity

5. **Keep Docker Desktop running** for K8s to work:
   - Kubernetes runs inside Docker Desktop
   - If Docker stops, K8s stops too

---

## 📚 Additional Resources

- **Docker Docs:** https://docs.docker.com/
- **Kubernetes Docs:** https://kubernetes.io/docs/
- **kubectl Cheat Sheet:** https://kubernetes.io/docs/reference/kubectl/cheatsheet/
- **BESCOM Report:** `BESCOMs-Carbon-Emissions-and-Energy-Mix.pdf` (in project folder)

---

**Good luck with your case study! 🌱🚀**

**Questions? Check the troubleshooting section or the logs first!**
