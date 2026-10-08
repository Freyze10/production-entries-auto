import psutil
import socket, os, getpass

def get_real_mac():
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for interface, addr_list in addrs.items():
        # Skip if interface is down
        if interface not in stats or not stats[interface].isup:
            continue

        for addr in addr_list:
            # AF_LINK = MAC address
            if addr.family == psutil.AF_LINK:
                mac = addr.address

                # Skip invalid or virtual MACs
                if mac and mac != "00:00:00:00:00:00":
                    # Optional: filter out VMware/VirtualBox
                    if not mac.lower().startswith(("00:50:56", "00:0c:29", "00:05:69")):
                        return mac.replace('-', ':')
    return None


def get_ethernet_ip():
    """Finds the IPv4 address specifically for the physical Ethernet adapter."""
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for interface, addr_list in addrs.items():
        # Skip if interface is down
        if interface not in stats or not stats[interface].isup:
            continue

        # Filter for typical Ethernet interface names (Windows usually names it 'Ethernet')
        # You can make this check looser if your adapter has a custom name, e.g., 'ethernet' in interface.lower()
        if "ethernet" in interface.lower():
            for addr in addr_list:
                # Check for IPv4
                if addr.family == socket.AF_INET:
                    return addr.address

    # Fallback: If no interface explicitly named "Ethernet" is found,
    # search for any active IPv4 that is NOT a loopback and NOT Tailscale (100.x.x.x)
    for interface, addr_list in addrs.items():
        if interface not in stats or not stats[interface].isup:
            continue

        for addr in addr_list:
            if addr.family == socket.AF_INET:
                ip = addr.address
                # Skip loopback and Tailscale CGNAT range (100.64.0.0/10)
                if not ip.startswith("127.") and not ip.startswith("100."):
                    return ip

    return 'N/A'

def _get_workstation_info():
    try:
        h = socket.gethostname()
    except:
        h = 'Unknown'

    # Use our custom function to target Ethernet specifically
    i = get_ethernet_ip()

    m = get_real_mac() or 'N/A'

    try:
        u = os.getlogin()
    except:
        u = getpass.getuser()

    full_user = f"{h}\\{u}"

    return {"h": h, "i": i, "m": m, "u": full_user}