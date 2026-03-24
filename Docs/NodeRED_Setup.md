# Node-RED Setup Guide
### ICS Water Simulation Lab — First Time Setup

This document covers how to fix permissions, open Node-RED for the first time, and import the lab flows. No prior Node-RED experience is required.

---

## Step 1 — Fix Folder Permissions

When you clone the project and start the containers for the first time, Docker creates the Node-RED data folder with root-only permissions. This must be fixed before Node-RED will work correctly.

Find the path to the Node-RED data folder in your cloned project (it will be inside the `revpi-twin` folder) and run:

```bash
sudo chown -R $USER:$USER /path/to/ics-water-simulation/revpi-twin
```

Replace `/path/to/` with your actual clone location. For example if you cloned into your home folder:

```bash
sudo chown -R $USER:$USER ~/ics-water-simulation/revpi-twin
```

Then restart the containers if not already running:

```bash
cd ~/ics-water-simulation
docker compose down
docker compose up -d --build
```

---

## Step 2 — Install Flow Dependencies

The lab flows require the `node-red-dashboard` package. Install it through the Node-RED palette manager:

1. Open Node-RED in your browser (`http://localhost:8080` or `http://10.10.10.52:8080`)
2. Click the **hamburger menu** (three horizontal lines) in the top-right corner
3. Select **Manage palette**
4. Click the **Install** tab
5. Search for `node-red-dashboard`
6. Click **Install** next to the package and wait for it to complete

> Node-RED will reload automatically once the package is installed.

---

## Step 3 — Open Node-RED

Once the containers are running, open Node-RED in your browser. Either URL works:

- `http://localhost:8080`
- `http://10.10.10.52:8080`

You should see the Node-RED editor — a blank canvas with a toolbar at the top and a panel of nodes on the left.

---

## Step 4 — Import the Lab Flows

The lab flows are pre-built and stored in the file `node-red-flows/flows_simulated.json`. You need to import this file into Node-RED once.

### 1. Open the import menu

Click the **hamburger menu** (three horizontal lines) in the top-right corner of the Node-RED editor.

```
☰  (top right corner)
```

Select **Import**.

### 2. Select the file

In the Import dialog that appears:

- Click **select a file to import**
- Navigate to your project folder and open `node-red-flows/flows_simulated.json`

### 3. Import

Click **Import** to confirm. The flows will appear on the canvas.

### 4. Deploy

Click the red **Deploy** button in the top-right corner to activate the flows.

```
[ Deploy ]  (top right, red button)
```

> If you do not click Deploy the flows are loaded but not running.

---

## Step 5 — Verify the Flows are Running

After deploying you should see the flows on the canvas with green status indicators under the nodes showing they are connected and active.

To confirm the lab simulation is running, check the tank simulator is responding:

```bash
http://localhost:8080/ui
```

---

## Understanding the Node-RED Interface

If this is your first time using Node-RED, here is a quick orientation:

| Element | Location | Purpose |
|---|---|---|
| Node palette | Left panel | Drag nodes onto the canvas to build flows |
| Canvas | Centre | Where flows are built and connected |
| Deploy button | Top right (red) | Activates changes — always click after editing |
| Hamburger menu | Top right (three lines) | Import, export, settings |
| Debug panel | Right panel (bug icon) | Shows output from Debug nodes |
| Info panel | Right panel (i icon) | Shows info about selected nodes |

### What is a flow?

A flow is a sequence of connected nodes. Data passes from left to right through the connections. Each node does something to the data — inject a message, run a command, send to a dashboard, etc.

### What is a node?

A node is a single building block. Double-click any node on the canvas to see and edit its configuration.

---

## Troubleshooting

**Node-RED won't open in the browser**

Check the container is running:

```bash
docker ps | grep node-red
```

If it is not listed, start the containers:

```bash
docker compose up -d --build
```

**Flows imported but nodes show red error indicators**

This usually means a dependency is missing. Check the Node-RED logs:

```bash
docker logs nuc-node-red --tail 30
```

**Permission denied errors in Node-RED logs**

Re-run the chown command from Step 1 and restart the containers:

```bash
sudo chown -R $USER:$USER ~/ics-water-simulation/node-red-flows
docker compose restart
```

**Changes not taking effect**

Always click the **Deploy** button after making any changes. Node-RED does not apply changes automatically.

---

*ICS Water Simulation Lab — Node-RED Setup Guide*
