# ELK Stack Setup for ICS Water Simulation (Ubuntu + Docker)

This document describes the complete setup of an ELK stack
(Elasticsearch, Logstash, Kibana) for the ICS Water Simulation project,
running on Ubuntu with Docker Compose.

The goal is to collect and visualize system logs using Filebeat and Logstash.

---

## Phase 0 – Prerequisites

- Ubuntu Desktop (GUI)
- Docker installed and running
- Docker Compose v2
- Internet access
- Project directory: `ics-water-simulation`

---

## Phase 1 – Network and Architecture Decisions

### Network Segmentation
Two Docker bridge networks are used to simulate ICS segmentation:

- OT / HMI Network: `10.10.10.0/24`
- Remote Management Network: `10.10.20.0/24`

---

## Phase 2 – Docker Compose Stack

### Services Included
- tank-sim – Water tank simulation
- revpi-twin – Node-RED digital twin
- hmi – Nginx-based HMI
- elasticsearch
- logstash
- kibana

---

## Phase 3 – ELK Deployment

### Start the stack
```bash
docker compose up -d
```

### Verify containers
```bash
docker compose ps
```

---

## Phase 4 – Logstash Pipeline Configuration

### Pipeline configuration
```conf
input {
  beats { port => 5044 }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "lab-beats-%{+YYYY.MM.dd}"
  }
}
```

---

## Phase 5 – Filebeat Installation

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https wget gpg
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update
sudo apt-get install -y filebeat
```

---

## Phase 6 – Filebeat Configuration

```bash
sudo filebeat modules enable system
sudo nano /etc/filebeat/filebeat.yml
```
Copy the file filebeat/filebeat.yml from the project

---

## Phase 7 – Verification

```bash
sudo filebeat test config
sudo filebeat test output
docker logs -f nuc-logstash
curl -s http://localhost:9200/_cat/indices?v
```

---

## Phase 8 – Kibana

- Open http://localhost:5601
- Create Data View: `lab-beats-*`
- Open Discover

---
## Phase 11 – Fix Filebeat "no enabled filesets" error (System module)

If Filebeat fails with an error similar to:

- `module system is configured but has no enabled filesets`

It means the `system` module is enabled, but its filesets (syslog/auth) are not enabled.

### Enable the module and verify
```bash
sudo filebeat modules enable system
sudo filebeat modules list
```

### Enable syslog and auth filesets
Edit the module configuration:
```bash
sudo nano /etc/filebeat/modules.d/system.yml
```

Minimum working configuration:
```yaml
- module: system
  syslog:
    enabled: true
  auth:
    enabled: true
```

If the file does not exist and only `system.yml.disabled` is present:
```bash
sudo mv /etc/filebeat/modules.d/system.yml.disabled /etc/filebeat/modules.d/system.yml
```

### Test and restart Filebeat
```bash
sudo filebeat test config -e
sudo systemctl reset-failed filebeat
sudo systemctl restart filebeat
sudo systemctl status filebeat --no-pager
```

### Confirm ingestion
Tail Logstash logs and confirm Beats events arrive:
```bash
docker logs -f nuc-logstash
```

