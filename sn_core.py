import os
import requests
import yaml
import shutil
import subprocess
import subprocess
import requests
from dataclasses import dataclass

@dataclass
class NetworkState:
    height: int = 0
    target_height: int = 0
    synced: bool = False

IMAGE = "ghcr.io/equilibriahorizon/equilibria-node:latest"
DOCKER_DOWNLOAD_URL = "https://www.docker.com/products/docker-desktop/"

def docker_exists():
    return shutil.which("docker") is not None

def is_container_running(name):
    """Checks status for a single container (used for registration validation)"""
    try:
        result = subprocess.run(
            f'docker inspect -f "{{{{.State.Running}}}}" {name}',
            shell=True, capture_output=True, text=True
        )
        return result.stdout.strip() == "true"
    except:
        return False
def restart_node(name):
    """Attempts to restart a specific container by name"""
    try:
        subprocess.run(f"docker start {name}", shell=True, check=True, capture_output=True)
        return True
    except Exception:
        return False
def get_all_nodes_status(count):
    """Optimized: Fetches all running container names in one command to avoid lag"""
    try:
        result = subprocess.run(
            'docker ps --format "{{.Names}}"',
            shell=True, capture_output=True, text=True, timeout=5
        )
        running_names = result.stdout.splitlines()
    except Exception:
        running_names = []

    status_list = []
    for i in range(1, count + 1):
        name = f"sn{i:02d}"
        # Check against local memory list instead of spawning new processes
        status_list.append("running" if name in running_names else "stopped")
    return status_list

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text
    except:
        return "127.0.0.1"

def create_compose(base, count, ip):
    services = {}
    for i in range(1, count + 1):
        num = f"{i:02d}"
        p2p, rpc, quo = 18090+((i-1)*2), 18091+((i-1)*2), 38160+(i-1)
        local_path = os.path.join(base, "data", f"sn{num}").replace("\\", "/")
        os.makedirs(local_path, exist_ok=True)
        
        services[f"sn{num}"] = {
            "image": IMAGE,
            "container_name": f"sn{num}",
            "restart": "unless-stopped",
            "tty": True,
            "stdin_open": True,
            "ports": [f"{p2p}:{p2p}", f"{rpc}:{rpc}", f"{quo}:{quo}"],
            "volumes": [f"{local_path}:/data"],
            "command": (f"--testnet --service-node --data-dir=/data --p2p-bind-ip=0.0.0.0 "
                        f"--p2p-bind-port={p2p} --rpc-admin=0.0.0.0:{rpc} "
                        f"--service-node-public-ip={ip} --quorumnet-port={quo} "
                        f"--l2-provider=http://84.247.143.210:8545 "
                        f"--add-priority-node=84.247.143.210:18080 --log-level=2")
        }
    with open(os.path.join(base, "docker-compose.yml"), "w") as f:
        yaml.dump({"services": services}, f, sort_keys=False)
    return True

def get_registration(selected_indices, amount, wallet):
    try:
        atomic = int(amount) * 1000000000
    except:
        return ["Error: Invalid amount format!"]

    results = []
    for i in selected_indices:
        rpc = 18091 + (i * 2)
        payload = {
            "jsonrpc": "2.0", "id": "0", "method": "get_service_node_registration_cmd",
            "params": {
                "operator_cut": "10.0", 
                "contributor_addresses": [wallet],
                "contributor_amounts": [atomic], 
                "staking_requirement": atomic
            }
        }
        try:
            response = requests.post(f"http://127.0.0.1:{rpc}/json_rpc", json=payload, timeout=8)
            r = response.json()
            if "result" in r:
                results.append(f"SN{i+1:02d} Command:\n{r['result']['registration_cmd']}")
            else:
                err = r.get("error", {}).get("message", "Node starting or not synced.")
                results.append(f"SN{i+1:02d} Error: {err}")
        except Exception:
            results.append(f"SN{i+1:02d} Error: Unreachable on port {rpc}. Wait 30s.")
    return results

def get_node_network_state(rpc_port):
    """Fetches blockchain height from the node to check sync status"""
    try:
        payload = {"jsonrpc": "2.0", "id": "0", "method": "get_info"}
        response = requests.post(f"http://127.0.0.1:{rpc_port}/json_rpc", json=payload, timeout=2)
        data = response.json()
        if "result" in data:
            res = data["result"]
            height = res.get("height", 0)
            target = res.get("target_height", 0)
            # Node is synced if it's within 2 blocks of target
            is_synced = height >= (target - 2) and target > 0
            return NetworkState(height, target, is_synced)
    except:
        pass
    return NetworkState()