import os
import platform
import subprocess
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

NETWORK_PATH = os.getenv("NETWORK_PATH")
NETWORK_USER = os.getenv("NETWORK_USER")
NETWORK_PASSWORD = os.getenv("NETWORK_PASSWORD")
NETWORK_MOUNT_POINT = os.getenv("NETWORK_MOUNT_POINT")


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_linux() -> bool:
    return platform.system() == "Linux"


def mount_network_windows(network_path: str, username: Optional[str] = None, password: Optional[str] = None) -> bool:
    if not network_path.startswith("\\\\"):
        network_path = "\\\\" + network_path.replace("/", "\\").lstrip("\\")
    
    try:
        if username and password:
            cmd = [
                "net", "use", network_path,
                f"/user:{username}", password
            ]
        else:
            cmd = ["net", "use", network_path]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0
        )
        
        return result.returncode == 0 or "already connected" in result.stdout.lower()
    except Exception:
        return False


def mount_network_linux(
    network_path: str,
    mount_point: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> bool:
    if not mount_point:
        mount_point = NETWORK_MOUNT_POINT or "/mnt/network_share"
    
    if not os.path.exists(mount_point):
        try:
            os.makedirs(mount_point, exist_ok=True, mode=0o755)
        except PermissionError:
            try:
                subprocess.run(["sudo", "mkdir", "-p", mount_point], check=True, capture_output=True)
                subprocess.run(["sudo", "chmod", "755", mount_point], check=True, capture_output=True)
            except Exception:
                return False
        except Exception:
            return False
    
    try:
        if os.path.ismount(mount_point):
            return True
    except Exception:
        pass
    
    if not network_path.startswith("//"):
        network_path = "//" + network_path.replace("\\", "/").lstrip("/")
    
    try:
        import pwd
        uid = os.getuid()
        gid = os.getgid()
    except Exception:
        uid = 1000
        gid = 1000
    
    mount_options = [f"uid={uid}", f"gid={gid}", "file_mode=0777", "dir_mode=0777"]
    
    if username and password:
        mount_options.append(f"username={username}")
        mount_options.append(f"password={password}")
    else:
        mount_options.append("guest")
    
    cmd = [
        "sudo", "mount", "-t", "cifs",
        network_path,
        mount_point,
        "-o", ",".join(mount_options)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return True
        
        if "already mounted" in result.stderr.lower() or "already mounted" in result.stdout.lower():
            return True
        
        return False
    except Exception:
        return False


def mount_network(
    network_path: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    mount_point: Optional[str] = None
) -> str:
    network_path = network_path or NETWORK_PATH
    username = username or NETWORK_USER
    password = password or NETWORK_PASSWORD
    
    if not network_path:
        raise ValueError("Network path not configured. Set NETWORK_PATH in .env file")
    
    if is_windows():
        if mount_network_windows(network_path, username, password):
            return network_path
        raise ConnectionError(f"Failed to mount network path: {network_path}")
    
    elif is_linux():
        mount_pt = mount_point or NETWORK_MOUNT_POINT or "/mnt/network_share"
        if mount_network_linux(network_path, mount_pt, username, password):
            return mount_pt
        raise ConnectionError(f"Failed to mount network path: {network_path} to {mount_pt}")
    
    else:
        raise OSError(f"Unsupported operating system: {platform.system()}")


def get_mounted_path(file_path: str, network_path: Optional[str] = None) -> str:
    network_path = network_path or NETWORK_PATH
    
    if not network_path:
        if os.path.isabs(file_path):
            return file_path
        raise ValueError("Network path not configured. Set NETWORK_PATH in .env file")
    
    if os.path.isabs(file_path):
        return file_path
    
    if is_windows():
        if not network_path.startswith("\\\\"):
            network_path = "\\\\" + network_path.replace("/", "\\").lstrip("\\")
        full_path = os.path.join(network_path, file_path).replace("/", "\\")
    else:
        mount_point = NETWORK_MOUNT_POINT or "/mnt/network_share"
        try:
            if not os.path.ismount(mount_point):
                mount_network(network_path)
        except Exception:
            pass
        file_path_normalized = file_path.replace("\\", "/")
        full_path = os.path.join(mount_point, file_path_normalized)
    
    return full_path

