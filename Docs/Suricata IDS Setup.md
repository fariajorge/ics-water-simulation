# Suricata IDS Setup for ICS Water Simulation (Ubuntu VM)

This document covers the installation and configuration of Suricata on the Ubuntu VM host to monitor Docker network traffic for the ICS Water Simulation lab.

---

## Phase 0 — Find Your Docker Bridge Interfaces

> Bridge names are unique per VM. Never copy them from another machine — always run these commands first.

```bash
# Set bridge names as variables for use throughout this setup
OT_BRIDGE=$(docker network inspect ics-water-simulation_ot_hmi_net --format '{{.Id}}' | cut -c1-12 | awk '{print "br-" $1}')
RM_BRIDGE=$(docker network inspect ics-water-simulation_rm_net --format '{{.Id}}' | cut -c1-12 | awk '{print "br-" $1}')

echo "OT bridge: $OT_BRIDGE"
echo "RM bridge: $RM_BRIDGE"
```

Keep these values — you will need them in every step below.

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

## Phase 2 — Prepare the Bridge Interfaces

Docker bridge interfaces require promiscuous mode and bridge netfilter to be enabled before Suricata can capture traffic on them.

```bash
# Enable promiscuous mode
sudo ip link set $OT_BRIDGE promisc on
sudo ip link set $RM_BRIDGE promisc on

# Enable bridge netfilter
sudo modprobe br_netfilter
sudo sysctl -w net.bridge.bridge-nf-call-iptables=1
sudo sysctl -w net.bridge.bridge-nf-call-ip6tables=1
```

---

## Phase 3 — Configure suricata.yaml

```bash
sudo nano /etc/suricata/suricata.yaml
```

### af-packet section

Find the `af-packet:` section and replace it with your bridge names:

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

Find the `pcap:` section and replace it with your bridge names:

```yaml
pcap:
  - interface: br-OT_BRIDGE      # replace with your ot_hmi_net bridge
    checksum-checks: no
  - interface: br-RM_BRIDGE      # replace with your rm_net bridge
    checksum-checks: no
  - interface: default
```

> `checksum-checks: no` is required — Docker virtual interfaces use offloaded checksums that Suricata cannot verify.

### Restart Suricata

```bash
sudo systemctl restart suricata
sudo systemctl status suricata --no-pager
```

---

## Phase 4 — Add the Local Rules File

Verify `local.rules` is referenced in suricata.yaml:

```bash
grep -n "local.rules" /etc/suricata/suricata.yaml
```

If the output is empty, add it manually:

```bash
sudo nano /etc/suricata/suricata.yaml
```

Find the `rule-files:` section and add:

```yaml
rule-files:
  - /etc/suricata/rules/local.rules
```

Create the file if it doesn't exist:

```bash
sudo touch /etc/suricata/rules/local.rules
```

---

## Phase 5 — Verify Suricata is Capturing Traffic

### Check interfaces are registered

```bash
sudo suricatasc -c iface-list
```

Both bridge interfaces should appear in the output.

### Check packet counters

```bash
sudo suricatasc -c dump-counters | python3 -m json.tool | grep '"pkts"' | head -5
```

Generate some traffic then run the command again — counters must be increasing. If they stay at 0, Suricata is not capturing on the right interface.

### Verify with tcpdump

```bash
sudo tcpdump -i $OT_BRIDGE -c 5 host 10.10.10.52
```

If tcpdump sees traffic but Suricata counters stay at 0, re-check the `af-packet` and `pcap` sections in suricata.yaml.

---

## Phase 6 — Allow Logstash to Read Logs

Since Logstash runs in Docker it reads `eve.json` via a bind mount. Make the log directory readable:

```bash
sudo chmod o+rx /var/log/suricata
sudo chmod o+r /var/log/suricata/eve.json
```

---

## Suricata is Ready

At this point Suricata is installed, monitoring both Docker networks, and ready for the lab exercises. Proceed to the lab document to write detection rules and run the attacks.
