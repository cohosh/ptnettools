#!/usr/bin/env python3

import argparse
import random
from yaml import load, dump

import lyrebird
import snowflake
import webtunnel

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def get_tor_path():
    return config['hosts']['4uthority1']['processes'][0]['path']

def main():
    parser = argparse.ArgumentParser(
        description="Extend a tornettols generated shadow config for PT experiments")
    parser.add_argument('--path', type=str, help='Path to the tornettools generated experiment directory')
    parser.add_argument('--transport', type=str, help='Name of the transport that is being tested')
    parser.add_argument('--transport-bin-path', type=str, help='Path to the transport binary (or folder containing multiple binaries)')
    parser.add_argument('--transport-stats-path', type=str, help='Path to transport specific metrics file')
    parser.add_argument('--china-perf-frac', type=float, default=0.0, help='Fraction of torperf clients to reassign to china network nodes')
    args = parser.parse_args()

    global config
    with open(args.path+"/shadow.config.yaml") as f:
        config = load(f, Loader=Loader)

    tor_path = get_tor_path()
    print(f"Found tor path: {tor_path}")

    if args.transport == "obfs4":
        config = lyrebird.update_config(args.path, tor_path, config, args.transport_bin_path)
    elif args.transport == "snowflake":
        config = snowflake.update_config(args.path, tor_path, config, args.transport_bin_path, args.transport_stats_path)
    elif args.transport == "webtunnel":
        config = webtunnel.update_config(args.path, tor_path, config, args.transport_bin_path)
    else:
        print(f"{args.transport} not supported. Currently supported transports are:\n" + \
                "obfs4\nsnowflake")
        exit(1)

    '''
    There are currently only 6 network nodes in the atlas graph with china country codes.
    You can grep the atlas file that tornettools uses to find them:
        $ xzcat {args.path}/conf/atlas_v201801.shadow_v2.gml.xz | grep -B 5 -A 3 CN
    '''
    if args.china_perf_frac > 0.0:
        china_net_ids = [304, 1094, 1568, 2115, 2139, 2423]

        all_perf_clients = [name for name in config['hosts'] if 'perfclient' in name]
        num_to_reassign = int(len(all_perf_clients) * args.china_perf_frac)

        if num_to_reassign > 0:
            print(f"Reassigning {num_to_reassign} perfclients to CN network nodes")
            for name in random.sample(all_perf_clients, num_to_reassign):
                config['hosts'][name]['network_node_id'] = random.choice(china_net_ids)

    print("Overwriting config...")
    with open(args.path+"/shadow.config.yaml", 'w') as f:
        dump(config, f, Dumper=Dumper)

if __name__ == '__main__':
    main()
