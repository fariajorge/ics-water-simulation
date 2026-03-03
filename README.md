# ICS Water Simulation Lab

A cybersecurity simulation lab built on Docker, modelling an Industrial Control System (ICS) water tank environment. The lab is designed for hands-on exercises in attack simulation, intrusion detection with Suricata, log analysis with the ELK stack, and incident response.

---

## Architecture Overview

```
OT/HMI Network (10.10.10.0/24)          RM Network (10.10.20.0/24)
┌─────────────────────────────┐          ┌──────────────────────────────┐
│  tank-sim      10.10.10.60  │          │  elasticsearch  10.10.20.10  │
│  revpi-twin    10.10.10.52  │◄────────►│  kibana         10.10.20.11  │
│  hmi           10.10.10.56  │          │  logstash       10.10.20.12  │
└─────────────────────────────┘          └──────────────────────────────┘
         ▲
         │  Suricata IDS (VM host)
         │  monitors both Docker bridge interfaces
```

---

## Network Reference

| Container | IP Address | Network | Port | Service |
|---|---|---|---|---|
| tank-sim | `10.10.10.60` | ot_hmi_net | 5000 | Tank simulator |
| revpi-twin | `10.10.10.52` | ot_hmi_net / rm_net | 1880 | Node-RED |
| hmi | `10.10.10.56` | ot_hmi_net | — | NGINX proxy |
| nuc-elasticsearch | `10.10.20.10` | rm_net | 9200 | Elasticsearch |
| nuc-kibana | `10.10.20.11` | rm_net | 5601 | Kibana |
| nuc-logstash | `10.10.20.12` | rm_net | 5044 | Logstash |

**VM host** acts as gateway for both networks:
- `10.10.10.1` — gateway for ot_hmi_net
- `10.10.20.1` — gateway for rm_net

---

## Prerequisites

- Ubuntu VM (tested on Ubuntu 24)
- Docker and Docker Compose installed
- Suricata installed on the VM host (see `Docs/Suricata_IDS_Setup.md`)
- Minimum 4GB RAM recommended (ELK stack is memory intensive)

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd ics-water-simulation
```

### 2. Fix Node-RED permissions

Docker creates the Node-RED data folder with root-only permissions on first clone. Fix this before starting the containers:

```bash
sudo chown -R $USER:$USER ~/ics-water-simulation/node-red-flows
```

### 3. Create the `.env` file

```bash
nano .env
```

Add your Kibana encryption keys (required for alerting):

```env
KIBANA_ENCRYPTION_KEY=your_key_here
KIBANA_REPORTING_KEY=your_key_here
KIBANA_SECURITY_KEY=your_key_here
```

Generate keys with:

```bash
docker exec -it nuc-kibana bin/kibana-encryption-keys generate
```

> The `.env` file is in `.gitignore` and will never be committed.

### 4. Start the lab

```bash
docker compose up -d --build
```

Wait about 60 seconds for Elasticsearch and Kibana to fully initialize.

### 5. Import Node-RED flows

Open Node-RED at `http://localhost:1880`, go to the hamburger menu (top right) → **Import**, and select `node-red-flows/flows_simulated.json`. Click **Deploy** when done.

> See `Docs/NodeRED_Setup.md` for detailed instructions with screenshots.

### 6. Start Suricata

```bash
sudo /usr/local/bin/suricata-start.sh
```

> This script auto-detects the Docker bridge interfaces and configures Suricata. Run it every time Docker is restarted. See `Docs/Suricata_IDS_Setup.md` for setup instructions.

### 7. Verify everything is running

```bash
# Check all containers are up
docker compose ps

# Check Suricata is capturing traffic
sudo suricatasc -c dump-counters | python3 -m json.tool | grep '"pkts"' | head -3

# Check Logstash is running
docker logs nuc-logstash --tail 10
```

---

## Accessing the Lab

| Service | URL |
|---|---|
| Node-RED (RevPi Twin) | `http://localhost:1880` |
| HMI | `http://localhost:8080` |
| Kibana | `http://localhost:5601` |
| Elasticsearch | `http://localhost:9200` |

---

## Stopping the Lab

```bash
docker compose down
```

> After restarting Docker, always run `sudo /usr/local/bin/suricata-start.sh` again — Docker recreates the bridge interfaces on every restart and Suricata needs to be updated with the new names.

---

## Project Structure

```
ics-water-simulation/
├── docker-compose.yml
├── .env                        # Kibana keys — not committed
├── .gitignore
├── README.md
├── Attack/                     # Attack scripts
├── Docs/                       # Lab documentation
│   ├── Suricata_IDS_Setup.md         # Suricata installation and config guide
│   ├── NodeRED_Setup.md              # Node-RED first time setup guide
│   ├── ICS_WaterTank_Lab.md          # Lab exercises
│   └── Exercise_Example_PingFlood.md # Worked example solution
├── elk/                        # ELK stack config
├── filebeat/                   # Filebeat config
├── hmi/                        # NGINX proxy config
├── node-red-flows/             # Node-RED flow definitions
├── revpi-twin/                 # RevPi Twin config
└── tank-sim/                   # Tank simulator application
```

---

## Documentation

| Document | Description |
|---|---|
| `Docs/Suricata_IDS_Setup.md` | How to install and configure Suricata on the VM host |
| `Docs/NodeRED_Setup.md` | Node-RED first time setup — permissions fix and flow import |
| `Docs/ICS_WaterTank_Lab.md` | Lab exercises — attack scenarios, Suricata rules, ELK analysis |
| `Docs/Exercise_Example_PingFlood.md` | Complete worked example — ping flood attack, detection rule, and incident report |

---

## Troubleshooting

**Containers not starting:**
```bash
docker compose logs
```

**Node-RED permission errors on first run:**
```bash
sudo chown -R $USER:$USER ~/ics-water-simulation/node-red-flows
docker compose restart
```

**Suricata not detecting traffic after Docker restart:**
```bash
sudo /usr/local/bin/suricata-start.sh
```

**Kibana not loading:**
```bash
docker logs nuc-kibana --tail 20
# Kibana takes ~60 seconds to start — wait and refresh
```

**No data in Kibana:**
```bash
# Check if the index exists
curl http://localhost:9200/_cat/indices

# Check Logstash is processing events
docker logs nuc-logstash --tail 20
```

**Suricata alerts not appearing in Kibana:**
```bash
# Check Suricata is writing alerts
tail -f /var/log/suricata/fast.log

# Check Logstash can read the log file
sudo chmod o+rx /var/log/suricata
sudo chmod o+r /var/log/suricata/eve.json
```
