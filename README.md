XeQ SN Factory - Service Node Testnet Installer
An automated deployment tool for Equilibria (XEQ) Service Nodes. This factory simplifies the process of setting up, managing, and registering multiple service nodes on a single Windows machine using Docker.
________________________________________
  Requirements
* **Windows 10/11**
* **Docker Desktop** (Must be running) - [Download here](https://www.docker.com/products/docker-desktop/)
* **Python 3.x** - [Download here](https://www.python.org/downloads/windows/) (Make sure to check "Add Python to PATH")

________________________________________
 Getting Started
1. Install Dependencies
Open your terminal (CMD or PowerShell) and run:
Bash
pip install pyyaml requests
2. Run the Application
Navigate to the project folder and run:
Bash
python main.py
3. Usage Steps
1.	Select Folder: Choose a directory where node data and configurations will be stored.
2.	Set Node Count: Enter how many Service Nodes you want to run.
3.	Start Nodes: Click START ALL NODES. This will generate the config and pull the latest Equilibria image.
4.	Wallet Setup: Use the OPEN WALLET CLI to create a new wallet or open an existing one.
5.	Register: Once nodes are synced, enter your wallet address and staking amount, then click GET REGISTRATION COMMANDS.
________________________________________
 Technical Architecture
The project consists of three main components:
•	main.py: The GUI controller and user interface.
•	sn_core.py: The engine handling Docker logic, IP discovery, and RPC communication.
•	Wallet_modal.py: A secure bridge to the xeq-wallet-cli running inside the Docker containers.
Port Mapping Logic
To avoid conflicts, the factory uses a dynamic port allocation system:
•	P2P Port: $18090 + (Index \times 2)$
•	RPC Port: $18091 + (Index \times 2)$
•	Quorumnet: $38160 + Index$
________________________________________
 Important Notes
•	Syncing: Nodes must be 100% synchronized before they can provide a registration command.
•	Public IP: The app automatically detects your public IP for the service-node-public-ip flag. Ensure your router/firewall allows the calculated ports.
•	Security: Temporary password files used for wallet access are automatically deleted after the terminal is closed.


<img width="2499" height="1479" alt="Screenshot (4)" src="https://github.com/user-attachments/assets/9e9dec2a-0be7-41da-85c8-5d642668b5fb" />
