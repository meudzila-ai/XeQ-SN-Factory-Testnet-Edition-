import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess, os, webbrowser, time, threading
from datetime import datetime
from Wallet_modal import wallet_modal
from sn_core import *

# --- Global variables ---
status_labels = []
last_sync_state = False  # Track sync status to prevent log spamming

# --- Functions ---

def copy_line_on_click(event):
    """Copies the double-clicked line to the clipboard"""
    try:
        # Determine the start and end of the clicked line
        line_index = event.widget.index(f"@{event.x},{event.y} linestart")
        line_end = event.widget.index(f"@{event.x},{event.y} lineend")
        text = event.widget.get(line_index, line_end).strip()
        if text:
            root.clipboard_clear()
            root.clipboard_append(text)
            # Visual confirmation in terminal
            print(f"Copied: {text}")
    except:
        pass

def add_right_click(widget):
    """Adds standard Cut/Copy/Paste context menu to a widget"""
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    widget.bind("<Button-3>", lambda event: menu.tk_popup(event.x_root, event.y_root))

def log_event(message):
    """Adds a timestamped message to the event log UI"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {message}\n"
    event_log.insert(tk.END, full_msg)
    event_log.see(tk.END)

def update_status_ui(stats):
    """Updates the color-coded health indicators for each node"""
    for i, s in enumerate(stats):
        if i >= len(status_labels): break
        try:
            color = "lightgreen" if s == "running" else "lightcoral"
            status_labels[i].config(bg=color)
        except:
            continue

def update_network_panel(stats_list):
    """Updates the network height and sync status UI based on active nodes"""
    global last_sync_state
    any_synced = False
    active_node_found = False
    
    for i, status in enumerate(stats_list):
        if status == "running":
            active_node_found = True
            rpc_port = 18091 + (i * 2)
            net_data = get_node_network_state(rpc_port)
            
            if net_data.height > 0:
                net_height_var.set(f"Block Height: {net_data.height} / {net_data.target_height}")
                if net_data.synced:
                    net_status_var.set("Network: ✅ SYNCED")
                    any_synced = True
                else:
                    net_status_var.set("Network: ⏳ SYNCING...")
                break # Extract data from the first responsive node

    if not active_node_found:
        net_height_var.set("Block Height: Offline")
        net_status_var.set("Network: ❌ NO NODES")

    # Registration button state control
    if any_synced:
        reg_btn.config(state="normal", bg="lightgreen", text="GET REGISTRATION COMMANDS")
    elif active_node_found:
        reg_btn.config(state="disabled", bg="lightgray", text="WAITING FOR SYNC...")
    else:
        reg_btn.config(state="disabled", bg="lightgray", text="START NODES TO REGISTER")

    # One-time notification when system becomes synced
    if any_synced and not last_sync_state:
        log_event("✨ System is fully synced. Registration is now available!")
        last_sync_state = True
    elif not any_synced:
        last_sync_state = False

def status_loop():
    """Background thread to monitor node status every 30 seconds"""
    while True:
        try:
            if not root.winfo_exists(): break
            node_count_str = nodes.get()
            if node_count_str and node_count_str.isdigit():
                count = int(node_count_str)
                current_stats = get_all_nodes_status(count)
                root.after(0, update_network_panel, current_stats)
                root.after(0, update_status_ui, current_stats)
                
                # Auto-restart crashed nodes if enabled
                if auto_restart_enabled.get():
                    for i, status in enumerate(current_stats):
                        if status == "stopped":
                            node_name = f"sn{i+1:02d}"
                            log_event(f"❌ CRASH: {node_name} is down. Restarting...")
                            restart_node(node_name)
        except Exception as e:
            print(f"Monitor error: {e}")
        time.sleep(30)

def browse():
    """Opens directory browser and detects existing node data"""
    path = filedialog.askdirectory()
    if path:
        folder.set(path)
        data_dir = os.path.join(path, "data")
        if os.path.exists(data_dir):
            existing = [d for d in os.listdir(data_dir) if d.startswith('sn') and os.path.isdir(os.path.join(data_dir, d))]
            if existing:
                nodes.set(str(len(existing)))
                update_checkboxes()

def check_docker():
    """Checks if Docker service is running; offers to start it if offline"""
    try:
        # Attempt to run a simple docker command to check service status
        subprocess.run("docker info", shell=True, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        # Prompt user to start Docker if not running
        answer = messagebox.askyesno("Docker Offline", "Docker Desktop is not running. Would you like to try starting it?")
        if answer:
            try:
                log_event("Attempting to start Docker Desktop...")
                # Standard Windows path for Docker Desktop
                os.startfile("C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe")
                
                messagebox.showinfo("Docker", "Docker Desktop initiated. Please wait ~30s for it to load, then press START again.")
                return False
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Docker automatically: {e}")
        return False
def check_for_update():
    """Checks if a newer Docker image is available and prompts for update"""
    try:
        base = folder.get()
        if not base: return

        log_event("Checking for node updates...")
        # 'docker compose pull' fetches the latest image metadata without starting containers
        result = subprocess.run("docker compose pull", cwd=base, shell=True, capture_output=True, text=True)
        
        # If the output contains 'Downloaded newer image', an update is available
        if "Downloaded newer image" in result.stdout or "Downloaded newer image" in result.stderr:
            ans = messagebox.askyesno("Update Available", "A new Service Node image was found! Would you like to apply the update now?\n\n(This will restart all nodes)")
            if ans:
                log_event("Updating nodes to the latest version...")
                # Restart nodes with the new image
                subprocess.run("docker compose up -d", cwd=base, shell=True)
                log_event("✅ All nodes have been updated and restarted.")
                messagebox.showinfo("Update Complete", "Nodes are now running on the latest version!")
            else:
                log_event("Update deferred by user.")
        else:
            log_event("Nodes are already up to date.")
    except Exception as e:
        print(f"Update check failed: {e}")
def start():
    if not check_docker():
        return

    base = folder.get()
    if not base or not nodes.get().isdigit():
        messagebox.showerror("Error", "Check folder and node count!")
        return

    bar["value"] = 10
    log_event(f"Starting deployment of {nodes.get()} nodes...")
    create_compose(base, int(nodes.get()), get_public_ip())

    bar["value"] = 50
    try:
        subprocess.run("docker compose up -d", cwd=base, shell=True, check=True, capture_output=True, text=True)
        bar["value"] = 100
        log_event("SUCCESS: All nodes launched.")
        
        # --- NEW: Check for updates immediately after starting ---
        root.after(1000, check_for_update) 
        
        messagebox.showinfo("Success", f"Launched {nodes.get()} nodes!")
    except subprocess.CalledProcessError as e:
        log_event(f"DOCKER ERROR: {e.stderr}")
        messagebox.showerror("Launch Failed", f"Docker error:\n{e.stderr}")

    if not check_docker():
        return

    base = folder.get()
    if not base or not nodes.get().isdigit():
        messagebox.showerror("Error", "Check folder and node count!")
        return

    bar["value"] = 10
    log_event(f"Starting deployment of {nodes.get()} nodes...")

    # Generate docker-compose.yml via core module
    create_compose(base, int(nodes.get()), get_public_ip())

    bar["value"] = 50

    try:
        # Launch containers in detached mode
        subprocess.run("docker compose up -d", cwd=base, shell=True, check=True, capture_output=True, text=True)
        bar["value"] = 100
        log_event("SUCCESS: All nodes launched.")
        messagebox.showinfo("Success", f"Launched {nodes.get()} nodes!")
    except subprocess.CalledProcessError as e:
        log_event(f"DOCKER ERROR: {e.stderr}")
        messagebox.showerror("Launch Failed", f"Docker error:\n{e.stderr}")

def register():
    """Generates CLI registration commands if validation passes"""
    # 1. Check if any nodes are selected
    selected = [i for i, var in enumerate(node_vars) if var.get()]
    if not selected:
        messagebox.showwarning("Selection Error", "Please select at least one node using the checkboxes!")
        return

    # 2. Check if the wallet address field is empty
    wallet_address = wallet.get().strip()
    if not wallet_address:
        messagebox.showwarning("Missing Information", "Please enter your Reward Wallet Address before generating commands.")
        e3.focus_set() 
        return

    # 3. Proceed with generation if validation passes
    out.delete("1.0", tk.END)
    log_event(f"Generating registration for {len(selected)} nodes...")
    
    try:
        res = get_registration(selected, amount.get(), wallet_address)
        for r in res:
            out.insert(tk.END, f"{r}\n\n")
        log_event("✅ Registration commands generated successfully.")
    except Exception as e:
        log_event(f"❌ Error generating commands: {e}")
        messagebox.showerror("Error", f"Failed to generate commands: {e}")

def update_checkboxes(*args):
    """Dynamically creates checkboxes and status dots based on node count"""
    for child in check_frame.winfo_children(): child.destroy()
    node_vars.clear()
    status_labels.clear()
    try:
        count = int(nodes.get() or 0)
        canvas = tk.Canvas(check_frame, height=65, highlightthickness=0)
        h_scroll = ttk.Scrollbar(check_frame, orient="horizontal", command=canvas.xview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(xscrollcommand=h_scroll.set)
        
        for i in range(count):
            var = tk.BooleanVar(value=True)
            node_vars.append(var)
            item_frame = tk.Frame(inner)
            item_frame.pack(side="left", padx=5)
            tk.Checkbutton(item_frame, text=f"SN{i+1:02d}", variable=var).pack()
            lbl = tk.Label(item_frame, text=" ", bg="gray", width=6, font=("Arial", 2))
            lbl.pack(fill="x")
            status_labels.append(lbl)
            
        canvas.pack(side="top", fill="x", expand=True)
        if count > 8: h_scroll.pack(side="bottom", fill="x")
    except: pass

# --- UI Setup ---
root = tk.Tk()
root.title("XeQ SN Factory v1.1")
root.iconbitmap("xeq.ico")
root.geometry("650x850")

# Variables for UI persistence
folder, nodes, wallet, amount = tk.StringVar(), tk.StringVar(value="1"), tk.StringVar(), tk.StringVar(value="100000")
net_height_var = tk.StringVar(value="Height: ---")
net_status_var = tk.StringVar(value="Status: Offline")

node_vars = []

# Progress Bar
bar = ttk.Progressbar(root, length=400, mode="determinate")
bar.pack(pady=10)

# Folder selection UI
tk.Label(text="Installation Folder:").pack()
f_frame = tk.Frame(root)
f_frame.pack()
e1 = tk.Entry(f_frame, textvariable=folder, width=40)
e1.pack(side="left")
add_right_click(e1)
tk.Button(f_frame, text="Browse", command=browse).pack(side="left")

# Node count UI
tk.Label(text="Number of Nodes:").pack(pady=(10,0))
e2 = tk.Entry(textvariable=nodes, width=10)
e2.pack()
add_right_click(e2)
nodes.trace_add("write", update_checkboxes)

# Container for node checkboxes
check_frame = tk.Frame(root, height=90)
check_frame.pack(pady=5, fill="x", padx=20)
check_frame.pack_propagate(False)

# Main action buttons
tk.Button(text="START ALL NODES", command=start, bg="lightblue", font=("Arial", 10, "bold"), width=30).pack(pady=5)
tk.Button(text="OPEN WALLET CLI", command=wallet_modal, bg="lightgray").pack(pady=5)

# Network status panel
info_frame = tk.Frame(root, bg="#2c3e50", padx=10, pady=5)
info_frame.pack(fill="x", padx=10, pady=5)
tk.Label(info_frame, textvariable=net_height_var, fg="white", bg="#2c3e50", font=("Arial", 10, "bold")).pack(side="left")
tk.Label(info_frame, textvariable=net_status_var, fg="white", bg="#2c3e50", font=("Arial", 10, "bold")).pack(side="right")

# Monitoring settings
auto_restart_enabled = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Enable Auto-Restart Monitor", variable=auto_restart_enabled, font=("Arial", 9, "italic"), fg="blue").pack()

# Event log display
event_log = tk.Text(height=6, width=80, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
event_log.pack(pady=5, padx=10)
add_right_click(event_log)
event_log.bind("<Double-1>", copy_line_on_click) 

# Registration inputs
tk.Label(text="Reward Wallet Address:").pack()
e3 = tk.Entry(textvariable=wallet, width=60)
e3.pack()
add_right_click(e3)

tk.Label(text="Staking Amount:").pack()
e4 = tk.Entry(textvariable=amount, width=20)
e4.pack()
add_right_click(e4)

# Dynamic registration button
reg_btn = tk.Button(text="START NODES TO REGISTER", command=register, bg="lightgray", state="disabled", font=("Arial", 10, "bold"), width=30)
reg_btn.pack(pady=5)

# Command output area
out_frame = tk.Frame(root)
out_frame.pack(pady=10, padx=10, fill="both", expand=True)

out_scroll = ttk.Scrollbar(out_frame)
out_scroll.pack(side="right", fill="y")

out = tk.Text(out_frame, height=8, width=80, bg="#f0f0f0", yscrollcommand=out_scroll.set)
out.pack(side="left", fill="both", expand=True)
add_right_click(out)

out_scroll.config(command=out.yview)

# Initialize checkboxes and start monitoring thread
update_checkboxes()
threading.Thread(target=status_loop, daemon=True).start()

root.mainloop()