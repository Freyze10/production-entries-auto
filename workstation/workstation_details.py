import psutil


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


def _get_workstation_info():
    import socket, os, getpass

    try:
        h = socket.gethostname()
        i = socket.gethostbyname(h)
    except:
        h, i = 'Unknown', 'N/A'

    m = get_real_mac() or 'N/A'

    try:
        u = os.getlogin()
    except:
        u = getpass.getuser()

    full_user = f"{h}\\{u}"

    return {"h": h, "i": i, "m": m, "u": full_user}