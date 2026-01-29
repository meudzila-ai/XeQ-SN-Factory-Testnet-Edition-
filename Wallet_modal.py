import subprocess
import tkinter as tk
from tkinter import messagebox
import os

def add_right_click(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

def wallet_modal():
    w = tk.Toplevel()
    w.title("Wallet Manager")
    w.iconbitmap("xeq.ico")
    w.geometry("420x450")
    mode = tk.StringVar(value="open")

    tk.Label(w, text="Equilibria Wallet Manager", font=('Arial', 11, 'bold')).pack(pady=10)
    tk.Radiobutton(w, text="Create New Wallet", variable=mode, value="new").pack()
    tk.Radiobutton(w, text="Open Existing Wallet", variable=mode, value="open").pack()

    tk.Label(w, text="Wallet Filename:").pack(pady=(15,0))
    name_ent = tk.Entry(w, width=35)
    name_ent.insert(0, "new_wallet")
    name_ent.pack(pady=5)
    add_right_click(name_ent)

    tk.Label(w, text="Password:").pack()
    pw = tk.Entry(w, show="*", width=35)
    pw.pack(pady=5)
    add_right_click(pw)

    def go(event=None):
        """Launches the wallet CLI inside the first node container"""
        if not pw.get() or not name_ent.get():
            messagebox.showwarning("Error", "Enter filename and password!")
            return

        # Using sn01 as the host for the CLI tool
        base_dir = os.path.join(os.getcwd(), "data", "sn01")
        os.makedirs(base_dir, exist_ok=True)
        pwd_file = os.path.join(base_dir, ".tmp_pwd")
        
        # Temporary password file for CLI automation
        with open(pwd_file, "w") as f: 
            f.write(pw.get())

        kill_old = "docker exec sn01 pkill -9 xeq-wallet-cli >nul 2>&1"
        
        if mode.get() == "new":
            wallet_cmd = f"docker exec -it sn01 /usr/local/bin/xeq-wallet-cli --testnet --generate-new-wallet=/data/{name_ent.get()} --password-file=/data/.tmp_pwd --use-english-language-names"
        else:
            wallet_cmd = f"docker exec -it sn01 /usr/local/bin/xeq-wallet-cli --testnet --wallet-file=/data/{name_ent.get()} --password-file=/data/.tmp_pwd --daemon-address=127.0.0.1:18091"

        # Launch in a new native command prompt window
        final_cmd = f'start "Equilibria Wallet" cmd /k "{kill_old} & {wallet_cmd} & del {pwd_file}"'
        subprocess.Popen(final_cmd, shell=True)
        w.destroy()

    # Bind Enter key for convenience
    name_ent.bind("<Return>", go)
    pw.bind("<Return>", go)

    tk.Button(w, text="LAUNCH WALLET", command=go, bg="#28a745", fg="white", font=('Arial', 10, 'bold'), width=25).pack(pady=25)

    
   
    