#!/usr/bin/env python3

import argparse
from yaml import load, dump

import lyrebird

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
    parser.add_argument('--transport-bin-path', type=str, help='Path for the transport binary')
    args = parser.parse_args()

    global config
    with open(args.path+"/shadow.config.yaml") as f:
        config = load(f, Loader=Loader)

    tor_path = get_tor_path()
    print(f"Found tor path: {tor_path}")

    match args.transport:
        case "obfs4":
            config = lyrebird.update_config(args.path, tor_path, config, args.transport_bin_path)
        case _:
            print(f"{args.transport} not supported. Currently supported transports are:\n \
                    obfs4")
            exit(1)

    print("Overwriting config...")
    with open(args.path+"/shadow.config.yaml", 'w') as f:
        dump(config, f, Dumper=Dumper)

if __name__ == '__main__':
    main()
