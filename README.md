# XeQ SN Factory v1.2
### (Automatic Updates • IP Watchdog • Crash Recovery)

A lightweight deployment factory for **Equilibria (XEQ)** Testnet Service Nodes.

This tool allows you to deploy, monitor, auto-update, and register multiple Service Nodes on a single Windows machine using Docker — with built-in watchdogs for crashes and public IP changes.

---

##  IMPORTANT — Safety First

* **TESTNET ONLY**
    This factory is strictly for Equilibria Testnet.
* **DO NOT REUSE MAINNET KEYS**
    Never use real wallet seeds, passwords, or addresses.
* **CREATE A FRESH TEST WALLET**
    Always use a brand-new empty wallet for testing.

---

## 🛠 Requirements

* **Windows 10 / 11 (64-bit)**
* **Docker Desktop (must be running)**
    [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
* **Python 3.x** (check *Add Python to PATH*)
    [Download Python](https://www.python.org/downloads/)

---

##  Getting Started

1.  **Install Dependencies:** Open your terminal (CMD or PowerShell) and run:
    ```bash
    pip install pyyaml requests
    ```
    *(Or double-click `install_requirements.bat` if available).*
2.  **Run the Application:** Run `python main.py` or double-click `run_factory.bat`.

---

##  Usage Steps

1.  **Select Folder:** Choose a directory where node data and configurations will be stored.
2.  **Set Node Count:** Enter how many Service Nodes you want to run.
3.  **Start Nodes:** Click **START ALL NODES**. This will verify Docker status, check for updates (v1.2), and pull the latest Equilibria image.
4.  **Wallet Setup:** Use the **OPEN WALLET CLI** to create a new wallet or open an existing one inside the container.
5.  **Get Commands:** Once nodes are synced (✅ SYNCED), enter your reward wallet address and staking amount, then click **GET REGISTRATION COMMANDS**.
6.  **Finalize Registration:** * Click on the generated command in the factory window (it will **Auto-Copy** to your clipboard).
    * Go to the **Wallet CLI terminal** (opened in step 4).
    * Paste the command and press **Enter** to confirm the staking transaction.

---

##  Technical Architecture

The project consists of three main components:
* **`main.py`**: The GUI controller and user interface.
* **`sn_core.py`**: The engine handling Docker logic, IP discovery, and RPC communication.
* **`Wallet_modal.py`**: A secure bridge to the `xeq-wallet-cli` running inside the Docker containers.

**Port Mapping Logic:**
To avoid conflicts, the factory uses a dynamic port allocation system:
* **P2P Port:** `18090 + (Index * 2)`
* **RPC Port:** `18091 + (Index * 2)`
* **Quorumnet:** `38160 + Index`

---

##  Important Notes

* **Syncing:** Nodes must be 100% synchronized before they can provide a registration command.
* **Public IP:** The app automatically detects your public IP. Ensure your router/firewall allows the calculated ports.
* **Security:** Temporary password files used for wallet access are automatically deleted after the wallet terminal is closed.

---
*Built for the community, making it easy for everyone to contribute!*