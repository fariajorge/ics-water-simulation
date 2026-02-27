# ELK Stack Setup for ICS Water Simulation (Ubuntu + Docker)

This document describes the complete setup of the ELK stack\
(Elasticsearch, Logstash, Kibana) for the ICS Water Simulation project,\
running on Ubuntu using Docker Compose.

The goal is to collect, process, and visualize system and container logs
using Filebeat and Logstash.

------------------------------------------------------------------------

## Phase 0 -- Prerequisites

-   Ubuntu Desktop or Server
-   Docker installed and running
-   Docker Compose v2
-   Internet access
-   Project directory: `ics-water-simulation`

Verify Docker:

``` bash
docker --version
docker compose version
```

------------------------------------------------------------------------

## Phase 1 -- Network and Architecture

### Network Segmentation

Two Docker bridge networks are used to simulate ICS segmentation:

-   OT / HMI Network: `10.10.10.0/24`
-   Remote Management Network: `10.10.20.0/24`

------------------------------------------------------------------------

## Phase 2 -- Docker Compose Stack

### Services Included

-   `tank-sim` -- Water tank simulation\
-   `revpi-twin` -- Node-RED digital twin\
-   `hmi` -- Nginx-based HMI\
-   `elasticsearch`\
-   `logstash`\
-   `kibana`

------------------------------------------------------------------------

## Phase 3 -- Deploy ELK Stack

### Start the stack

``` bash
docker compose up -d --build
```

### Verify containers

``` bash
docker compose ps
```

All services should be in the `Up` state.

------------------------------------------------------------------------

## Phase 4 -- Logstash Pipeline Configuration

Logstash receives logs from Filebeat via port `5044` and forwards them
to Elasticsearch.

Pipeline files are located in:

    elk/logstash/pipeline/

After editing:

``` bash
docker compose restart logstash
```

------------------------------------------------------------------------

## Phase 5 -- Install Filebeat on Ubuntu

``` bash
sudo apt-get update
sudo apt-get install -y apt-transport-https wget gpg

wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg

echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list

sudo apt-get update
sudo apt-get install -y filebeat
```

------------------------------------------------------------------------

## Phase 6 -- Configure Filebeat

### Enable System Module

``` bash
sudo filebeat modules enable system
sudo filebeat modules list
```

### Enable syslog and auth filesets

``` bash
sudo nano /etc/filebeat/modules.d/system.yml
```

Minimum configuration:

``` yaml
- module: system
  syslog:
    enabled: true
  auth:
    enabled: true
```

If only `system.yml.disabled` exists:

``` bash
sudo mv /etc/filebeat/modules.d/system.yml.disabled /etc/filebeat/modules.d/system.yml
```

------------------------------------------------------------------------

### Configure filebeat.yml

``` bash
sudo nano /etc/filebeat/filebeat.yml
```

Copy configuration from:

    filebeat/filebeat.yml

inside the project repository.

------------------------------------------------------------------------

### Docker Container Logs Input

Copy:

    filebeat/inputs.d/docker-container.yml

to:

    /etc/filebeat/inputs.d/

------------------------------------------------------------------------

## Phase 7 -- Test and Start Filebeat

``` bash
sudo filebeat test config -e
sudo filebeat test output

sudo systemctl reset-failed filebeat
sudo systemctl restart filebeat
sudo systemctl status filebeat --no-pager
```

------------------------------------------------------------------------

## Phase 8 -- Verify Ingestion

### Check Logstash receives events

``` bash
docker logs -f nuc-logstash
```

### Check Elasticsearch indices

``` bash
curl -s http://localhost:9200/_cat/indices?v
```

You should see:

    lab-beats-YYYY.MM.dd

------------------------------------------------------------------------

## Phase 9 -- Kibana Visualization

Open:

    http://localhost:5601

### Create Data View

1.  Go to **Stack Management**
2.  Click **Data Views**
3.  Create new data view: `lab-beats-*`
4.  Select `@timestamp`
5.  Save

### View Logs

1.  Go to **Discover**
2.  Select `lab-beats-*`
3.  Set time range to "Last 15 minutes"

You should now see system and container logs indexed.

------------------------------------------------------------------------

## Architecture Summary

-   Filebeat collects system and container logs from Ubuntu.
-   Logs are sent to Logstash on port 5044.
-   Logstash processes and forwards logs to Elasticsearch.
-   Kibana visualizes indexed data.

This setup provides centralized log monitoring for the ICS Water
Simulation environment.

