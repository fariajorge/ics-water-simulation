# Suricata IDS Setup for ICS Water Simulation (Ubuntu VM)

This document covers the installation and configuration of Suricata on the Ubuntu VM host to monitor Docker network traffic for the ICS Water Simulation lab.

---

## Phase 1 — Install Suricata

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install suricata -y
```

Verify:

```bash
suricata --build-info
sudo systemctl status suricata --no-pager
```

---

## Phase 2 — Configure suricata.yaml

```bash
sudo nano /etc/suricata/suricata.yaml
```

### af-packet section

Find the `af-packet:` section and replace it with the following. Use your actual bridge IDs from `docker network ls`:

```yaml
af-packet:
  - interface: br-xxxxxxxxxxxx    # ot_hmi_net
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
  - interface: br-xxxxxxxxxxxx    # rm_net
    cluster-id: 98
    cluster-type: cluster_flow
    defrag: yes
  - interface: default
```

### pcap section

Find the `pcap:` section and replace it with the following:

```yaml
pcap:
  - interface: br-xxxxxxxxxxxx    # ot_hmi_net
    checksum-checks: no
  - interface: br-xxxxxxxxxxxx    # rm_net
    checksum-checks: no
  - interface: default
```

> **The comments `# ot_hmi_net` and `# rm_net` are required** — the startup script uses them as anchors to update the bridge IDs automatically. Do not remove them.

> Do NOT use `eth0` or `enp0s3` — those are the VM's internet interface and cannot see Docker container traffic.

> `checksum-checks: no` is required — Docker virtual interfaces use offloaded checksums that Suricata cannot verify.

### Find your bridge IDs

```bash
docker network ls | grep ics-water-simulation
```

Example output:
```
79565f873712   ics-water-simulation_ot_hmi_net   bridge    local
b14454781180   ics-water-simulation_rm_net       bridge    local
```

Prefix with `br-` to get the interface name: `br-79565f873712`, `br-b14454781180`.

> **This is a one-time manual step.** After this, the startup script handles all future updates automatically.

---

## Phase 3 — Add the Local Rules File

Verify `local.rules` is referenced in suricata.yaml:

```bash
grep -n "local.rules" /etc/suricata/suricata.yaml
```

If the output is empty, open suricata.yaml, find the `rule-files:` section and add:

```yaml
rule-files:
  - /etc/suricata/rules/local.rules
```

Create the file if it doesn't exist:

```bash
sudo touch /etc/suricata/rules/local.rules
```

---

## Phase 4 — Allow Logstash to Read Logs

Since Logstash runs in Docker it reads `eve.json` via a bind mount. Make the log directory readable:

```bash
sudo chmod o+rx /var/log/suricata
sudo chmod o+r /var/log/suricata/eve.json
```

---

## Phase 5 — Create the Startup Script

> **Why this is needed:** Docker bridge interface names change every time Docker recreates the networks. This script auto-detects the current bridge names and updates Suricata's config before starting — so after the first-time manual setup in Phase 2, you never need to touch `suricata.yaml` again.

Create the script:

```bash
sudo nano /usr/local/bin/suricata-start.sh
```

Paste the following:

```bash
#!/bin/bash
# Auto-detect Docker bridge interfaces and start Suricata

OT_BRIDGE=$(docker network inspect ics-water-simulation_ot_hmi_net --format '{{.Id}}' | cut -c1-12 | awk '{print "br-" $1}')
RM_BRIDGE=$(docker network inspect ics-water-simulation_rm_net --format '{{.Id}}' | cut -c1-12 | awk '{print "br-" $1}')

echo "OT bridge: $OT_BRIDGE"
echo "RM bridge: $RM_BRIDGE"

# Update suricata.yaml using comment anchors to target the correct lines
# This works because the comments # ot_hmi_net and # rm_net never change
sudo sed -i "s/interface: br-[a-f0-9]*.*# ot_hmi_net/interface: $OT_BRIDGE    # ot_hmi_net/" /etc/suricata/suricata.yaml
sudo sed -i "s/interface: br-[a-f0-9]*.*# rm_net/interface: $RM_BRIDGE    # rm_net/" /etc/suricata/suricata.yaml

echo "suricata.yaml updated"

# Enable promiscuous mode on bridges
sudo ip link set $OT_BRIDGE promisc on
sudo ip link set $RM_BRIDGE promisc on

# Enable bridge netfilter
sudo modprobe br_netfilter
sudo sysctl -w net.bridge.bridge-nf-call-iptables=1
sudo sysctl -w net.bridge.bridge-nf-call-ip6tables=1

# Restart Suricata
sudo systemctl restart suricata
sudo systemctl status suricata --no-pager
```

Make it executable:

```bash
sudo chmod +x /usr/local/bin/suricata-start.sh
```

---

## Starting Suricata

Every time you start the lab or after a Docker restart, run:

```bash
sudo /usr/local/bin/suricata-start.sh
```

This handles bridge detection, promiscuous mode, and Suricata restart automatically. Safe to run multiple times.

---

## Verifying Suricata is Capturing Traffic

```bash
# Check interfaces are registered
sudo suricatasc -c iface-list

# Check rules are loaded
sudo suricatasc -c ruleset-stats

# Watch alerts in real time
tail -f /var/log/suricata/fast.log

# Check alerts in Elasticsearch
curl -s "http://localhost:9200/suricata-eve-*/_search?pretty" -H "Content-Type: application/json" -d '{
  "query": { "term": { "event_type": "alert" } },
  "size": 5,
  "sort": [{ "@timestamp": { "order": "desc" } }]
}'
```

---

## Suricata is Ready

At this point Suricata is installed, monitoring both Docker networks, and ready for the lab exercises. Proceed to the lab document to write detection rules and run the attacks.
