import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess, os, webbrowser, time, threading
from datetime import datetime
from Wallet_modal import wallet_modal
from sn_core import *

status_labels = []
node_vars = []
all_selected = False  
last_deployed_ip = None  

def copy_to_clipboard(text):
    """Copies clean text to clipboard without hidden terminal formatting"""
    root.clipboard_clear()
    clean_text = text.strip()
    root.clipboard_append(clean_text)
    root.update()
    log_event(f"COPIED: Command ready for terminal.")

def copy_line_on_click(event):
    """Detects clicked line and triggers clean copy"""
    try:
        line_index = event.widget.index(f"@{event.x},{event.y} linestart")
        line_end = event.widget.index(f"@{event.x},{event.y} lineend")
        text = event.widget.get(line_index, line_end).strip()
        if text and not text.startswith("SN"):
            copy_to_clipboard(text)
    except:
        pass

def add_right_click(widget):
    """Standard context menu"""
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    widget.bind("<Button-3>", lambda event: menu.tk_popup(event.x_root, event.y_root))

def log_event(message):
    """Unified logging with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {message}\n"
    event_log.insert(tk.END, full_msg)
    event_log.see(tk.END)

def check_for_update():
    """Checks if a newer Docker image is available and updates if found"""
    log_event("Checking for node updates...")
    try:
        base = folder.get()
        if not base: return False

        result = subprocess.run(
            "docker compose pull",
            cwd=base,
            shell=True,
            capture_output=True,
            text=True
        )

        output = (result.stdout or "") + (result.stderr or "")

        if "Downloaded" in output or "Pull complete" in output:
            log_event("Update found. Restarting nodes...")
            subprocess.run(
                "docker compose up -d",
                cwd=base,
                shell=True
            )
            messagebox.showinfo("Update", "New version pulled and nodes restarted.")
            return True
        else:
            log_event("Nodes already up to date.")
            return False
    except Exception as e:
        log_event(f"Update check failed: {e}")
        return False

def toggle_all_nodes():
    """Toggles selection for all node checkboxes"""
    global all_selected
    all_selected = not all_selected
    for var in node_vars:
        var.set(all_selected)
    
    toggle_btn.config(text="DESELECT ALL" if all_selected else "SELECT ALL")
    log_event(f"WATCHDOG: All nodes {'selected' if all_selected else 'deselected'}.")

def check_docker():
    """Confirms Docker Desktop is active"""
    try:
        subprocess.run("docker info", shell=True, check=True, capture_output=True)
        return True
    except:
        log_event("ERROR: Docker Desktop is not responding.")
        msg = "Docker Desktop is not running!\n\nWould you like to try starting it automatically?"
        if messagebox.askyesno("Docker Offline", msg):
            try:
                log_event("Attempting to launch Docker Desktop...")
                docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
                if os.path.exists(docker_path):
                    os.startfile(docker_path)
                    log_event("Launch command sent. Wait ~1-2 mins.")
                else:
                    log_event("CRITICAL: Docker path not found.")
            except Exception as e:
                log_event(f"Launch failed: {e}")
        return False

def hard_restart_docker():
    """Emergency: Restarts the Docker Desktop process"""
    if messagebox.askyesno("Emergency Restart", "This will kill all Docker processes and restart. Continue?"):
        try:
            log_event("RESTART: Killing Docker Desktop...")
            subprocess.run("taskkill /F /IM \"Docker Desktop.exe\"", shell=True, capture_output=True)
            time.sleep(2)
            check_docker() 
        except Exception as e:
            log_event(f"Restart failed: {e}")

def update_status_ui(stats):
    """Updates the visual indicators (green/red)"""
    for i, s in enumerate(stats):
        if i >= len(status_labels): break
        color = "lightgreen" if s == "running" else "lightcoral"
        status_labels[i].config(bg=color)

def update_network_panel(stats_list):
    """Main monitor: checks sync status"""
    active_found = False
    for i, status in enumerate(stats_list):
        if status == "running":
            active_found = True
            rpc_port = 18091 + (i * 2)
            net_data = get_node_network_state(rpc_port)
            if net_data.height > 0:
                net_height_var.set(f"Height: {net_data.height} / {net_data.target_height}")
                if net_data.synced:
                    net_status_var.set("Network: ✅ SYNCED")
                    reg_btn.config(state="normal", bg="lightgreen", text="GET REGISTRATION COMMANDS")
                else:
                    net_status_var.set("Network: ⏳ SYNCING...")
                    reg_btn.config(state="disabled", bg="lightgray", text="WAITING FOR SYNC...")
                break
    if not active_found:
        net_height_var.set("Height: Offline")
        net_status_var.set("Network: ❌ NO NODES")
        reg_btn.config(state="disabled", bg="lightgray", text="CREATE NODES TO REGISTER")

def ip_watchdog():
    """Background loop to monitor Public IP and auto-fix nodes if IP changes"""
    global last_deployed_ip
    while True:
        try:
            new_ip = get_public_ip()
            current_ip_var.set(f"Public IP: {new_ip}")
            
            if last_deployed_ip and new_ip != last_deployed_ip:
                log_event(f"⚠️ IP CHANGE DETECTED! New IP: {new_ip}")
                if auto_restart_enabled.get():
                    log_event("WATCHDOG: Auto-migrating nodes to new IP...")
                    base = folder.get()
                    selected = [i for i, var in enumerate(node_vars) if var.get()]
                    if base and selected:
                        create_compose(base, selected, new_ip)
                        subprocess.run("docker compose up -d --remove-orphans", cwd=base, shell=True, capture_output=True)
                        last_deployed_ip = new_ip
                        log_event("✅ WATCHDOG: Nodes migrated successfully.")
            
            time.sleep(60) 
        except:
            time.sleep(10)

def status_loop():
    """Background watchdog for node crashes"""
    while True:
        try:
            if not root.winfo_exists(): break
            node_count_str = nodes.get()
            if node_count_str.isdigit():
                count = int(node_count_str)
                current_stats = get_all_nodes_status(count)
                root.after(0, update_network_panel, current_stats)
                root.after(0, update_status_ui, current_stats)
                if auto_restart_enabled.get():
                    for i, status in enumerate(current_stats):
                        if status == "stopped":
                            name = f"sn{i+1:02d}"
                            log_event(f"WATCHDOG: {name} down! Restarting...")
                            restart_node(name)
        except: pass
        time.sleep(15)

def start():
    """Main deployment logic"""
    global last_deployed_ip
    if not check_docker(): return
    base = folder.get()
    selected = [i for i, var in enumerate(node_vars) if var.get()]
    if not base or not selected:
        messagebox.showerror("Error", "Select folder and at least one SN checkbox!")
        return
    
    # Run the auto-update check during start
    check_for_update()

    current_ip = get_public_ip()
    bar["value"] = 10
    log_event(f"Deploying on IP: {current_ip}...")
    create_compose(base, selected, current_ip)
    bar["value"] = 50
    try:
        subprocess.run("docker compose up -d --remove-orphans", cwd=base, shell=True, check=True, capture_output=True)
        last_deployed_ip = current_ip
        bar["value"] = 100
        log_event("DEPLOYMENT SUCCESSFUL.")
    except Exception as e:
        log_event(f"CRITICAL ERROR: {e}")

def register():
    """Generates commands for the output window"""
    selected = [i for i, var in enumerate(node_vars) if var.get()]
    if not selected:
        messagebox.showwarning("No Selection", "Please check the SN boxes you want to register.")
        return
        
    wallet_addr = wallet.get().strip()
    if not wallet_addr:
        messagebox.showwarning("Error", "Enter reward wallet address.")
        return
        
    out.delete("1.0", tk.END)
    res = get_registration(selected, amount.get(), wallet_addr)
    for r in res:
        out.insert(tk.END, f"{r}\n\n")
    out.focus_set()
    log_event(f"Commands ready for {len(selected)} nodes.")

def browse():
    """Select folder and detect existing nodes"""
    path = filedialog.askdirectory()
    if path:
        folder.set(path)
        data_dir = os.path.join(path, "data")
        if os.path.exists(data_dir):
            existing = [d for d in os.listdir(data_dir) if d.startswith('sn') and os.path.isdir(os.path.join(data_dir, d))]
            if existing:
                count = len(existing)
                nodes.set(str(count))
                log_event(f"FOLDER: Detected {count} existing nodes.")
                update_checkboxes()

def update_checkboxes(*args):
    """Updates SN selection checkboxes"""
    for child in check_frame.winfo_children(): child.destroy()
    node_vars.clear()
    status_labels.clear()
    try:
        val = nodes.get()
        count = int(val) if val.isdigit() else 0
        canvas = tk.Canvas(check_frame, height=65, highlightthickness=0)
        h_scroll = ttk.Scrollbar(check_frame, orient="horizontal", command=canvas.xview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(xscrollcommand=h_scroll.set)
        for i in range(count):
            var = tk.BooleanVar(value=all_selected)
            node_vars.append(var)
            item = tk.Frame(inner); item.pack(side="left", padx=5)
            tk.Checkbutton(item, text=f"SN{i+1:02d}", variable=var).pack()
            lbl = tk.Label(item, text=" ", bg="gray", width=6, font=("Arial", 2))
            lbl.pack(fill="x")
            status_labels.append(lbl)
        canvas.pack(side="top", fill="x", expand=True)
        if count > 8: h_scroll.pack(side="bottom", fill="x")
    except: pass

# --- UI Build ---
root = tk.Tk()
root.title("XeQ SN Factory v1.2")
root.iconbitmap("xeq.ico")
root.geometry("650x920")

folder, nodes = tk.StringVar(), tk.StringVar(value="0")
wallet, amount = tk.StringVar(), tk.StringVar(value="100000")
net_height_var, net_status_var = tk.StringVar(value="Height: ---"), tk.StringVar(value="Status: Offline")
current_ip_var = tk.StringVar(value="Detecting IP...")

bar = ttk.Progressbar(root, length=400, mode="determinate"); bar.pack(pady=10)

tk.Label(text="Installation Folder:").pack()
f_frame = tk.Frame(root); f_frame.pack()
f_ent = tk.Entry(f_frame, textvariable=folder, width=40)
f_ent.pack(side="left")
add_right_click(f_ent)
tk.Button(f_frame, text="Browse", command=browse).pack(side="left")

tk.Label(text="Number of Nodes:").pack(pady=(10,0))
n_ent = tk.Entry(textvariable=nodes, width=10)
n_ent.pack()
add_right_click(n_ent)
nodes.trace_add("write", update_checkboxes)

toggle_btn = tk.Button(root, text="SELECT ALL", command=toggle_all_nodes, font=("Arial", 8, "bold"), bg="#f8f9fa")
toggle_btn.pack(pady=(10, 0))

check_frame = tk.Frame(root, height=90); check_frame.pack(pady=5, fill="x", padx=20)
check_frame.pack_propagate(False)

tk.Button(text="START / UPDATE SELECTED NODES", command=start, bg="lightblue", font=("Arial", 10, "bold"), width=35).pack(pady=5)

e_row = tk.Frame(root); e_row.pack(pady=5)
tk.Button(e_row, text="RESTART DOCKER", command=hard_restart_docker, bg="#e74c3c", fg="white", font=("Arial", 8)).pack(side="left", padx=5)
tk.Button(e_row, text="OPEN WALLET CLI", command=wallet_modal, bg="lightgray").pack(side="left", padx=5)

info_frame = tk.Frame(root, bg="#2c3e50", padx=10, pady=5); info_frame.pack(fill="x", padx=10, pady=5)
tk.Label(info_frame, textvariable=current_ip_var, fg="yellow", bg="#2c3e50", font=("Arial", 9, "bold")).pack(side="left")
tk.Label(info_frame, textvariable=net_height_var, fg="white", bg="#2c3e50", font=("Arial", 9)).pack(side="left", padx=20)
tk.Label(info_frame, textvariable=net_status_var, fg="white", bg="#2c3e50", font=("Arial", 9, "bold")).pack(side="right")

auto_restart_enabled = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Enable Auto-Watchdog (IP & Crash protection)", variable=auto_restart_enabled).pack()

event_log = tk.Text(height=8, width=80, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9)); event_log.pack(pady=5, padx=10)
add_right_click(event_log)

tk.Label(text="Reward Wallet Address:").pack()
w_ent = tk.Entry(textvariable=wallet, width=60)
w_ent.pack()
add_right_click(w_ent)

tk.Label(text="Staking Amount:").pack()
a_ent = tk.Entry(textvariable=amount, width=20)
a_ent.pack()
add_right_click(a_ent)

reg_btn = tk.Button(text="CREATE NODES TO REGISTER", command=register, bg="lightgray", state="disabled", font=("Arial", 10, "bold"), width=30)
reg_btn.pack(pady=5)

# Output with Scrollbar
out_frame = tk.Frame(root)
out_frame.pack(pady=10, padx=10, fill="both", expand=True)
out_scroll = ttk.Scrollbar(out_frame)
out_scroll.pack(side="right", fill="y")
out = tk.Text(out_frame, height=10, width=80, bg="#f0f0f0", font=("Consolas", 10), yscrollcommand=out_scroll.set)
out.pack(side="left", fill="both", expand=True)
out_scroll.config(command=out.yview)
out.bind("<Button-1>", copy_line_on_click)
add_right_click(out)

update_checkboxes()
threading.Thread(target=status_loop, daemon=True).start()
threading.Thread(target=ip_watchdog, daemon=True).start()
root.mainloop()