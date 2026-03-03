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

Find the `af-packet:` section and replace it with the following:

```yaml
af-packet:
  - interface: br-OT_BRIDGE      # replace with your ot_hmi_net bridge
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
  - interface: br-RM_BRIDGE      # replace with your rm_net bridge
    cluster-id: 98
    cluster-type: cluster_flow
    defrag: yes
  - interface: default
```

> Do NOT use `eth0` or `enp0s3` — those are the VM's internet interface and cannot see Docker container traffic.

### pcap section

Find the `pcap:` section and replace it with the following:

```yaml
pcap:
  - interface: br-OT_BRIDGE      # replace with your ot_hmi_net bridge
    checksum-checks: no
  - interface: br-RM_BRIDGE      # replace with your rm_net bridge
    checksum-checks: no
  - interface: default
```

> `checksum-checks: no` is required — Docker virtual interfaces use offloaded checksums that Suricata cannot verify.

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

> **Why this is needed:** Docker bridge interface names (e.g. `br-cd88b0e118f3`) are generated from the network ID and change every time Docker recreates the networks. This script auto-detects the current bridge names and updates Suricata's config before starting it — so you never have to manually edit `suricata.yaml` again.

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

# Update suricata.yaml with current bridge names
sudo sed -i "s/br-[a-f0-9]\{12\}/$OT_BRIDGE/g" /etc/suricata/suricata.yaml
sudo sed -i "s/br-[a-f0-9]\{12\}/$RM_BRIDGE/g" /etc/suricata/suricata.yaml

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

This handles bridge detection, promiscuous mode, and Suricata restart automatically.

---

## Suricata is Ready

At this point Suricata is installed, monitoring both Docker networks, and ready for the lab exercises. Proceed to the lab document to write detection rules and run the attacks.
