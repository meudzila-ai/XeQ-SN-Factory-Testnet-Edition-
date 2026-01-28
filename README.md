#  XeQ SN Factory - Service Node Testnet Installer

An automated deployment tool for **Equilibria (XEQ)** Service Nodes. This factory simplifies the process of setting up, managing, and registering multiple service nodes on a single Windows machine using Docker.

###  Requirements
* **OS:** Windows 10/11 (64-bit)
* **Docker Desktop:** (Must be running) - [Download here](https://www.docker.com/products/docker-desktop/)
* **Python 3.x:** [Download here](https://www.python.org/downloads/) (Make sure to check **"Add Python to PATH"**)

###  IMPORTANT: Safety First
* **TESTNET ONLY:** This tool is strictly for the Equilibria Testnet. Do not attempt to use it for Mainnet nodes.
* **DO NOT REUSE KEYS:** Never use the same passwords, seeds, or private keys that you use for your **Mainnet** (real funds) wallet.
* **STAY SAFE:** Always create a brand new, empty wallet specifically for testing purposes.

---

###  Getting Started
1. **Install Dependencies:** Double-click `install_requirements.bat`. This will automatically install `pyyaml` and `requests`.
2. **Run the Application:** Double-click `run_factory.bat` to launch the GUI.

---

###  Usage Steps
1. **Select Folder:** Choose a directory where node data and configurations will be stored.
2. **Set Node Count:** Enter how many Service Nodes you want to run.
3. **Start Nodes:** Click **START ALL NODES**. This will generate the configuration and pull the latest Equilibria image.
4. **Wallet Setup:** Use the **OPEN WALLET CLI** to create a new wallet or open an existing one inside the container.
5. **Register:** Once nodes are synced, enter your wallet address and staking amount, then click **GET REGISTRATION COMMANDS**.

---

###  Technical Architecture
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

###  Important Notes
* **Syncing:** Nodes must be 100% synchronized before they can provide a registration command.
* **Public IP:** The app automatically detects your public IP. Ensure your router/firewall allows the calculated ports.
* **Security:** Temporary password files used for wallet access are automatically deleted after the wallet terminal is closed.

---
*Built for the community, making it easy for everyone to contribute!* 
