
def assign_ip(config):
    assigned_ips = {host['ip_addr'] for host in config['hosts'].values() if 'ip_addr' in host}
    for a in range(1, 256):
        for b in range(1, 256):
            for c in range(1, 256):
                for d in range(1, 256):
                    ip = f"{a}.{b}.{c}.{d}"
                    if ip not in assigned_ips:
                        return ip
    else:
        print("No available IPs")
        exit(1)

def write_torrc(path, torrc):
    with open(path, 'w', encoding="utf-8") as f:
        f.write(torrc)

