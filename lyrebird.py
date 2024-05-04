import os

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

def generate_server_torrc(path):
    torrc = "BridgeRelay 1\n" + \
        "ORPort 9001 IPv4Only\n" + \
        "ServerTransportListenAddr obfs4 0.0.0.0:8443\n" + \
        f"ServerTransportPlugin obfs4 exec {path}\n"
    return torrc

def generate_client_torrc(path, ip):
    torrc = "UseBridges 1\n" + \
        "UseEntryGuards 1\n" + \
        f"ClientTransportPlugin obfs4 exec {path}\n" + \
        f"Bridge obfs4 {ip}:8443 cert=u9i4Els/5iMAL0OD5Lu9MBDjxJE/zEa116D35obufc0NYTWBgRLf3qur92WL9hmN30J1Bw iat-mode=0"
    return torrc

def write_torrc(path, torrc):
    with open(path, 'w', encoding="utf-8") as f:
        f.write(torrc)

def create_bridge_host(path, tor_path, bridge_ip, config):
    # Add bridge to shadow config
    config['hosts']['bridge'] = {
        'network_node_id': 1,
        'ip_addr': bridge_ip,
        'bandwidth_down': '10000000 kilobit',
        'bandwidth_up': '10000000 kilobit',
        'processes': [
            {
                'path': tor_path,
                'args': "--defaults-torrc torrc-defaults -f ../../../conf/server.pt.torrc",
                'start_time': 3,
                'expected_final_state': 'running'
            } #TODO: do we want to add oniontrace to this bridge??
        ]
    }

    # Add a template directory for the bridge
    os.makedirs(path+"/shadow.data.template/hosts/bridge/pt_state/")
    with open(path+"/shadow.data.template/hosts/bridge/pt_state/obfs4_state.json",
              'w', encoding="utf-8") as f:
        f.write('{"node-id":"bbd8b8125b3fe623002f4383e4bbbd3010e3c491","private-key":"7467926c07b81820c7f6c0572bbc6614a639ff34013db8a38de3f5dc4dacf8f5","public-key":"3fcc46b5d7a0f7e686ee7dcd0d6135818112dfdeababf7658bf6198ddf427507","drbg-seed":"d1f43aa5e63a59d1aa2f8ccd73671e994097b9f93ee4cb0d","iat-mode":0}')
    with open(path+"/shadow.data.template/hosts/bridge/torrc-defaults",
              'w', encoding="utf-8") as f:
        f.write("# The following files specify default tor config options for this host.\n" + \
                "%include ../../../conf/tor.common.torrc\n" + \
                "%include ../../../conf/tor.relay.torrc\n" +  \
                "%include ../../../conf/tor.relay.guardonly.torrc\n" + \
                "BandwidthRate 1073741824\n" + \
                "BandwidthBurst 1073741824")

    return config

def update_config(path, tor_path, config, bin_path):

    bridge_ip = assign_ip(config)
    write_torrc(path+"/conf/server.pt.torrc", generate_server_torrc(bin_path))
    write_torrc(path+"/conf/client.pt.torrc", generate_client_torrc(bin_path, bridge_ip))

    config = create_bridge_host(path, tor_path, bridge_ip, config)
    # Update perf clients to use client.pt.torrc
    for host in config['hosts']:
        if host.startswith('perfclient'):
            config['hosts'][host]['processes'][0]['args'] = config['hosts'][host]['processes'][0]['args'] + " -f ../../../conf/client.pt.torrc"

    return config
