import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess, os, webbrowser, time
from Wallet_modal import wallet_modal
from sn_core import *

def add_right_click(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    
    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)
        
    widget.bind("<Button-3>", show_menu)

def browse():
    path = filedialog.askdirectory()
    if path:
        folder.set(path)
        data_dir = os.path.join(path, "data")
        if os.path.exists(data_dir):
            existing = [d for d in os.listdir(data_dir) if d.startswith('sn') and os.path.isdir(os.path.join(data_dir, d))]
            if existing:
                nodes.set(str(len(existing)))
                update_checkboxes()

def start():
    base = folder.get()
    if not base:
        messagebox.showerror("Error", "Please select a folder!")
        return
    
    if not docker_exists():
        if messagebox.askyesno("Docker Missing", "Docker not found. Open download page?"):
            webbrowser.open(DOCKER_DOWNLOAD_URL)
        return

    try:
        subprocess.run("docker ps", shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        if messagebox.askyesno("Docker Offline", "Docker Desktop is not running. Would you like to start it?"):
            docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
            if os.path.exists(docker_path):
                os.startfile(docker_path)
                messagebox.showinfo("Starting Docker", "Docker Desktop is starting... Please wait a minute, then click START ALL NODES again.")
            else:
                messagebox.showerror("Error", "Could not find Docker Desktop.exe. Start it manually.")
            return
        else: return

    bar["value"] = 20
    root.update()
    create_compose(base, int(nodes.get()), get_public_ip())
    bar["value"] = 60
    root.update()
    
    try:
        subprocess.run("docker compose up -d", cwd=base, shell=True, check=True, capture_output=True, text=True)
        bar["value"] = 100
        root.update()
        messagebox.showinfo("Success", f"Launched {nodes.get()} nodes!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Launch Failed", f"Docker error:\n{e.stderr}")

def register():
    selected = [i for i, var in enumerate(node_vars) if var.get()]
    if not selected:
        messagebox.showwarning("Error", "Select at least one node!")
        return

    offline = [f"sn{i+1:02d}" for i in selected if not is_container_running(f"sn{i+1:02d}")]
    if offline:
        messagebox.showerror("Nodes Offline", f"These nodes are not running: {', '.join(offline)}")
        return

    out.delete("1.0", tk.END)
    out.insert(tk.END, "Connecting to nodes... This might take a few seconds...\n")
    root.update()
    
    res = get_registration(selected, amount.get(), wallet.get())
    out.delete("1.0", tk.END)
    for r in res: out.insert(tk.END, f"{r}\n\n")

def update_checkboxes(*args):
    for child in check_frame.winfo_children(): child.destroy()
    node_vars.clear()
    try:
        count = int(nodes.get() or 0)
        canvas = tk.Canvas(check_frame, height=45, highlightthickness=0)
        h_scroll = ttk.Scrollbar(check_frame, orient="horizontal", command=canvas.xview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(xscrollcommand=h_scroll.set)
        for i in range(count):
            var = tk.BooleanVar(value=True)
            node_vars.append(var)
            tk.Checkbutton(inner, text=f"SN{i+1:02d}", variable=var).pack(side="left", padx=5)
        canvas.pack(side="top", fill="x", expand=True)
        if count > 8: h_scroll.pack(side="bottom", fill="x")
    except: pass

# --- UI Setup ---
root = tk.Tk()
root.title("XeQ SN Factory")
folder, nodes, wallet, amount = tk.StringVar(), tk.StringVar(value="1"), tk.StringVar(), tk.StringVar(value="100000")
node_vars = []

bar = ttk.Progressbar(root, length=400, mode="determinate")
bar.pack(pady=10)

tk.Label(text="Installation Folder:").pack()
f_frame = tk.Frame(root)
f_frame.pack()
e1 = tk.Entry(f_frame, textvariable=folder, width=40)
e1.pack(side="left")
add_right_click(e1)
tk.Button(f_frame, text="Browse", command=browse).pack(side="left")

tk.Label(text="Number of Nodes:").pack(pady=(10,0))
e2 = tk.Entry(textvariable=nodes, width=10)
e2.pack()
add_right_click(e2)
nodes.trace_add("write", update_checkboxes)

check_frame = tk.Frame(root, height=75, width=500)
check_frame.pack(pady=5, fill="x", padx=20)
check_frame.pack_propagate(False)

tk.Button(text="START ALL NODES", command=start, bg="lightblue", font=("Arial", 10, "bold"), width=30).pack(pady=10)
tk.Button(text="OPEN WALLET CLI", command=wallet_modal, bg="lightgray").pack(pady=5)

tk.Label(text="Reward Wallet Address:").pack()
e3 = tk.Entry(textvariable=wallet, width=60)
e3.pack()
add_right_click(e3)

tk.Label(text="Staking Amount:").pack()
e4 = tk.Entry(textvariable=amount, width=20)
e4.pack()
add_right_click(e4)

tk.Button(text="GET REGISTRATION COMMANDS", command=register, bg="lightgreen", font=("Arial", 10, "bold"), width=30).pack(pady=10)

out = tk.Text(height=10, width=85, bg="#f0f0f0")
out.pack(pady=10, padx=10)
add_right_click(out)

update_checkboxes()
root.mainloop()