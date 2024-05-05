import util

import os

def generate_server_torrc(path):
    torrc = "BridgeRelay 1\n" + \
        "ORPort 9001 IPv4Only\n" + \
        "ServerTransportListenAddr snowflake 0.0.0.0:8080\n" + \
        f"ServerTransportPlugin snowflake exec {path} -disable-tls\n"
    return torrc

def generate_client_torrc(path):
    torrc = "UseBridges 1\n" + \
        "UseEntryGuards 1\n" + \
        f"ClientTransportPlugin snowflake exec {path} -keep-local-addresses -log pt.log -unsafe-logging\n" + \
        f"Bridge snowflake 192.0.2.1:80 ice=stun:stun:3478 url=http://broker:8080"
    return torrc

def create_bridge_host(path, tor_path, config):
    config['hosts']['bridge'] = {
        'network_node_id': 1,
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
    os.makedirs(path+"/shadow.data.template/hosts/bridge/")
    with open(path+"/shadow.data.template/hosts/bridge/torrc-defaults",
              'w', encoding="utf-8") as f:
        f.write("# The following files specify default tor config options for this host.\n" + \
                "%include ../../../conf/tor.common.torrc\n" + \
                "%include ../../../conf/tor.relay.torrc\n" +  \
                "%include ../../../conf/tor.relay.guardonly.torrc\n" + \
                "BandwidthRate 1073741824\n" + \
                "BandwidthBurst 1073741824")
    return config

def create_broker_host(path, exp_path, config):
    # Add broker to shadow config
    config['hosts']['broker'] = {
        'network_node_id': 1,
        'bandwidth_down': '10000000 kilobit',
        'bandwidth_up': '10000000 kilobit',
        'processes': [
            {
                'path': path + "/broker",
                'args': '-addr ":8080" -disable-tls -unsafe-logging -allowed-relay-pattern ^bridge$ -bridge-list-path bridge-list.json',
                'start_time': 1,
                'expected_final_state': 'running'
            }
        ]
    }
    # Add bridge-list.json file to shadow template directory
    os.makedirs(exp_path+"/shadow.data.template/hosts/broker/")
    with open(exp_path+"/shadow.data.template/hosts/broker/bridge-list.json",
              'w', encoding="utf-8") as f:
        f.write('{"displayName":"localhost", "webSocketAddress":"ws://bridge:8080", "fingerprint":"2B280B23E1107BB62ABFC40DDCC8824814F80A72"}')
    return config

def create_stun_host(path, config):
    config['hosts']['stun'] = {
        'network_node_id': 1,
        'bandwidth_down': '10000000 kilobit',
        'bandwidth_up': '10000000 kilobit',
        'processes': [
            {
                'path': path + "/stund",
                'start_time': 1,
                'expected_final_state': 'running'
            }
        ]
    }
    return config

def create_proxy_hosts(path, config):
    for i in range(0,25):
        config['hosts']['proxy'+str(i)] = {
            'network_node_id': 1,
            'bandwidth_down': '10000000 kilobit',
            'bandwidth_up': '10000000 kilobit',
            'processes': [
                {
                    'path': path + "/proxy",
                    'args': "-verbose -unsafe-logging -keep-local-addresses -broker http://broker:8080 -relay ws://bridge:8080 -stun stun:stun:3478 -allowed-relay-hostname-pattern ^bridge$ -allow-non-tls-relay -nat-probe-server http://probetest:8443/probe",
                    'start_time': 3,
                    'expected_final_state': 'running'
                }
            ]
        }
    return config

def create_probetest_host(path, config):
    config['hosts']['probetest'] = {
        'network_node_id': 1,
        'bandwidth_down': '10000000 kilobit',
        'bandwidth_up': '10000000 kilobit',
        'processes': [
            {
                'path': path + "/probetest",
                'args': "-disable-tls -stun stun:stun:3478",
                'start_time': 1,
                'expected_final_state': 'running'
            }
        ]
    }
    return config

def validate_bin_path(path):
    #check to see that all the binaries we need are in the folder of the path
    if not (os.path.exists(path+"/client") and os.path.exists(path+"/proxy") and
         os.path.exists(path+"/server") and os.path.exists(path+"/broker") and
         os.path.exists(path+"/stund") and os.path.exists(path+"/probetest")):
        print(f"To generate snowflake experiments, make sure to build and install all of the snowflake binaries into the same directory pointed to by the --transport-bin-path option. You will need the following binaries: client, proxy, server, broker, probetest, stund. See the README for more information.")
        exit(1)


def update_config(path, tor_path, config, bin_path, stats_path):
    validate_bin_path(bin_path)
    util.write_torrc(path+"/conf/server.pt.torrc", generate_server_torrc(bin_path+"/server"))
    util.write_torrc(path+"/conf/client.pt.torrc", generate_client_torrc(bin_path+"/client"))

    config = create_broker_host(bin_path, path, config)
    config = create_stun_host(bin_path, config)
    config = create_bridge_host(path, tor_path, config)
    config = create_proxy_hosts(bin_path, config)
    config = create_probetest_host(bin_path, config)
    # Update perf clients to use client.pt.torrc
    for host in config['hosts']:
        if host.startswith('perfclient'):
            config['hosts'][host]['processes'][0]['args'] = config['hosts'][host]['processes'][0]['args'] + " -f ../../../conf/client.pt.torrc"

    return config

