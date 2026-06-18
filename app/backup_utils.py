import os
import subprocess
import datetime
from pathlib import Path
from tkinter import messagebox
import threading


_MYSQLDUMP_CANDIDATES = [
    r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqldump.exe",
    r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
    r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe",
    r"C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
    r"C:\Program Files (x86)\MySQL\MySQL Server 5.7\bin\mysqldump.exe",
    r"C:\xampp\mysql\bin\mysqldump.exe",
    r"D:\xampp\mysql\bin\mysqldump.exe",
    r"C:\wamp64\bin\mysql\mysql8.0.36\bin\mysqldump.exe",
    r"C:\wamp64\bin\mysql\mysql8.0.31\bin\mysqldump.exe",
    r"C:\wamp\bin\mysql\mysql8.0.31\bin\mysqldump.exe",
]


def _find_mysqldump() -> str:
    """Return path to mysqldump: check PATH first, then known install locations."""
    # 1. Already on PATH?
    try:
        result = subprocess.run(["mysqldump", "--version"],
                                capture_output=True, timeout=5)
        if result.returncode == 0:
            return "mysqldump"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 2. Known fixed locations
    for candidate in _MYSQLDUMP_CANDIDATES:
        if Path(candidate).exists():
            return candidate

    # 3. Scan WAMP for any installed MySQL version dynamically
    for wamp_root in [r"C:\wamp64\bin\mysql", r"C:\wamp\bin\mysql"]:
        wamp_path = Path(wamp_root)
        if wamp_path.exists():
            for version_dir in sorted(wamp_path.iterdir(), reverse=True):
                candidate = version_dir / "bin" / "mysqldump.exe"
                if candidate.exists():
                    return str(candidate)

    # 4. Scan standard MySQL program files for any version dynamically
    for mysql_root in [r"C:\Program Files\MySQL", r"C:\Program Files (x86)\MySQL"]:
        mysql_path = Path(mysql_root)
        if mysql_path.exists():
            for version_dir in sorted(mysql_path.iterdir(), reverse=True):
                candidate = version_dir / "bin" / "mysqldump.exe"
                if candidate.exists():
                    return str(candidate)

    return None


def create_database_backup(app, parent_widget=None, on_complete=None):
    """
    Creates a MySQL database dump using mysqldump and saves it locally.
    """
    # Create backups directory
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = app.config_data.db_name
    filename = f"backup_{db_name}_{timestamp}.sql"
    filepath = backup_dir / filename
    
    # Locate mysqldump executable
    mysqldump_exe = _find_mysqldump()

    # Pre-flight check — fail fast with a helpful message
    if not mysqldump_exe:
        messagebox.showerror(
            "mysqldump Not Found",
            "The 'mysqldump' tool was not found on this system.\n\n"
            "Fix options:\n"
            "1. Install MySQL: https://dev.mysql.com/downloads/installer/\n"
            "2. Add MySQL bin folder to Windows PATH\n"
            "3. XAMPP users: add C:\\xampp\\mysql\\bin to PATH\n"
            "4. WAMP users: add C:\\wamp64\\bin\\mysql\\<version>\\bin to PATH\n\n"
            "After installing, restart this application.",
            parent=parent_widget
        )
        if on_complete:
            on_complete()
        return

    # Build mysqldump command
    cmd = [
        mysqldump_exe,
        f"--host={app.config_data.db_host}",
        f"--port={app.config_data.db_port}",
        f"--user={app.config_data.db_user}",
    ]
    
    # Avoid passing password on command line if possible, but for simplicity on Windows desktop:
    if app.config_data.db_password:
        cmd.append(f"--password={app.config_data.db_password}")
        
    cmd.append(db_name)
    
    def run_backup():
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                # Calculate size
                try:
                    size_bytes = filepath.stat().st_size
                    size_str = f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024 * 1024 else f"{size_bytes / (1024 * 1024):.2f} MB"
                except Exception:
                    size_str = "Unknown"
                
                try:
                    app.db.log_backup(filename, str(filepath.absolute()), "Success", size_str)
                except Exception as ex:
                    print(f"Failed to log backup to DB: {ex}")

                # Need to update UI from main thread
                app.after(0, lambda: messagebox.showinfo(
                    "Backup Successful", 
                    f"Database backup created successfully!\n\nFile saved to: {filepath.absolute()}", 
                    parent=parent_widget
                ))
                if on_complete:
                    app.after(0, on_complete)
            else:
                err_msg = result.stderr
                # Check if mysqldump is not recognized
                if "not recognized" in err_msg or "not found" in err_msg.lower():
                    err_msg = "The 'mysqldump' tool is not installed or not in PATH.\nPlease install MySQL Command Line Tools to use this feature."
                
                try:
                    app.db.log_backup(filename, str(filepath.absolute()), "Failed", "0 KB")
                except Exception as ex:
                    print(f"Failed to log failed backup to DB: {ex}")

                app.after(0, lambda: messagebox.showerror(
                    "Backup Failed", 
                    f"Failed to create backup.\n\nError: {err_msg}", 
                    parent=parent_widget
                ))
                # Delete empty file if failed
                if filepath.exists():
                    filepath.unlink()
                if on_complete:
                    app.after(0, on_complete)
                    
        except FileNotFoundError:
            try:
                app.db.log_backup(filename, str(filepath.absolute()), "Failed", "0 KB")
            except Exception:
                pass
            app.after(0, lambda: messagebox.showerror(
                "Backup Failed",
                "The 'mysqldump' tool was not found.\n\n"
                "Checked locations:\n"
                "  - System PATH\n"
                "  - C:\\Program Files\\MySQL\\...\\bin\\\n"
                "  - C:\\xampp\\mysql\\bin\\\n"
                "  - C:\\wamp64\\bin\\mysql\\...\\bin\\\n\n"
                "Fix options:\n"
                "1. Install MySQL: https://dev.mysql.com/downloads/installer/\n"
                "2. Add MySQL bin folder to Windows PATH environment variable\n"
                "3. For XAMPP: add C:\\xampp\\mysql\\bin to PATH\n"
                "4. For WAMP: add C:\\wamp64\\bin\\mysql\\<version>\\bin to PATH",
                parent=parent_widget
            ))
            if filepath.exists():
                filepath.unlink()
            if on_complete:
                app.after(0, on_complete)
        except Exception as e:
            try:
                app.db.log_backup(filename, str(filepath.absolute()), "Failed", "0 KB")
            except Exception:
                pass
            app.after(0, lambda: messagebox.showerror(
                "Backup Failed", 
                f"An error occurred during backup:\n{str(e)}", 
                parent=parent_widget
            ))
            if filepath.exists():
                filepath.unlink()
            if on_complete:
                app.after(0, on_complete)

    # Run in background to prevent freezing UI
    thread = threading.Thread(target=run_backup)
    thread.daemon = True
    thread.start()
