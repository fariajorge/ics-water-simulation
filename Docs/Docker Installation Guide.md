# Docker Installation Guide for Ubuntu (README)

This document explains how to correctly install **Docker Engine (Docker CE)** on any Ubuntu system (Desktop or Server).  
These steps work on Ubuntu **22.04** and **24.04**.

---

## 1. Update your system

```bash
sudo apt update
sudo apt upgrade -y
```

---

## 2. Install required packages

```bash
sudo apt install ca-certificates curl gnupg -y
```

---

## 3. Add Docker’s official GPG key

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

---

## 4. Add the Docker repository

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

---

## 5. Update package list again

```bash
sudo apt update
```

---

## 6. Install Docker Engine

```bash
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```

---

## 7. Allow Docker to run without sudo

```bash
sudo usermod -aG docker $USER
```

**Important:** Log out and back in, or reboot:

```bash
sudo reboot
```

---

## 8. Test Docker

After logging back in:

```bash
docker run hello-world
```

If you see **Hello from Docker!**, the installation was successful.

---

## Notes

- This installs **Docker Engine**, not Docker Desktop.
- Works perfectly inside virtual machines.
- Required for ICS projects, digital twins, Node‑RED, ELK, and containerized labs.

---

## End

