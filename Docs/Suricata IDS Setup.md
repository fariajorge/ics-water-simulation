# Suricata IDS Setup for ICS Water Simulation (Ubuntu VM)

This document describes the complete setup of Suricata IDS for the ICS
Water Simulation project, running directly on Ubuntu.

The goal is to monitor VM network traffic and forward structured logs
(eve.json) to the ELK stack running in Docker, with verification
performed in Kibana.

------------------------------------------------------------------------

## Phase 0 -- Prerequisites

-   Ubuntu VM
-   Internet access
-   Docker ELK stack already running
-   Network interface identified (example: enp0s3)

------------------------------------------------------------------------

## Phase 1 -- Install Suricata

### Update system

``` bash
sudo apt update
sudo apt upgrade -y
```

### Install Suricata

``` bash
sudo apt install suricata -y
```

### Verify installation

``` bash
suricata --build-info
```

### Check service status

``` bash
sudo systemctl status suricata --no-pager
```

------------------------------------------------------------------------

## Phase 2 -- Configure Network Interface

Identify active interface:

``` bash
ip a
```

Example interface in this VM:

    enp0s3

Edit configuration:

``` bash
sudo nano /etc/suricata/suricata.yaml
```

Locate the AF-Packet section:

``` yaml
af-packet:
  - interface: eth0
```

Replace with:

``` yaml
af-packet:
  - interface: enp0s3
```

Restart Suricata:

``` bash
sudo systemctl restart suricata
```

Verify:

``` bash
sudo systemctl status suricata --no-pager
```

------------------------------------------------------------------------

## Phase 3 -- Enable eve.json Logging

Open configuration:

``` bash
sudo nano /etc/suricata/suricata.yaml
```

Ensure the following section is enabled:

``` yaml
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert
        - dns
        - flow
        - http
```

Restart:

``` bash
sudo systemctl restart suricata
```

------------------------------------------------------------------------

## Phase 4 -- Generate Test Traffic

Generate DNS and HTTP traffic to create events:

``` bash
ping -c 3 8.8.8.8
curl http://example.com
```

Optional alert testing:

``` bash
curl http://testmyids.com
```

------------------------------------------------------------------------

## Phase 5 -- Allow Docker Logstash to Read Logs

Since Logstash runs in Docker, it must access the host log file.

``` bash
sudo chmod o+rx /var/log/suricata
sudo chmod o+r /var/log/suricata/eve.json
```

------------------------------------------------------------------------

## Phase 6 -- Verify Logs in Kibana

### 1. Open Kibana

Open in browser:

    http://localhost:5601

If accessing from another machine:

    http://<VM-IP>:5601

------------------------------------------------------------------------

### 2. Create Data View

-   Go to **Stack Management**
-   Click **Data Views**
-   Click **Create data view**
-   Name it: `suricata-eve-*`
-   Select `@timestamp` as the time field
-   Click **Save**

------------------------------------------------------------------------

### 3. Verify Events in Discover

-   Go to **Discover**
-   Select the `suricata-eve-*` data view
-   Set time range to **Last 15 minutes**
-   Search for:

```{=html}
<!-- -->
```
    event.module:suricata

You should see Suricata events such as:

-   event_type: dns
-   event_type: flow
-   event_type: alert

To view only alerts:

    event_type: alert

------------------------------------------------------------------------

## Phase 7 -- Architecture Summary

Suricata runs directly on the Ubuntu VM and monitors the network
interface using AF-Packet.

Logs are written to:

/var/log/suricata/eve.json

Logstash (Docker) reads the log file via bind mount and forwards events
to Elasticsearch.

Kibana is used to visualize and analyze Suricata IDS events.

