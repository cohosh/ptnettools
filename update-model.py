import sys
import getopt
import lzma

import networkx as nx

def usage(f = sys.stdout):
    print(f"""\
Usage:
    {sys.argv[0]} [OPTION...] network-model.gml.xz

Options:
    -h --help       show this help
""", file = f)


def read_graph(path):
    with lzma.open(path) as f:
        print(f"Reading compressed network graph")
        network = nx.readwrite.gml.read_gml(f, label='id')
        print("Finished reading network graph")
        return network

# Returns a list of node ids that correspond to that country code
def find_nodes(network, cc):
    bottleneck_nodes = [id for (id, data) in network.nodes(data=True) if 'country_code' in data and data['country_code'].casefold() == cc.casefold()]
    return bottleneck_nodes

def make_directed(network):
    return network.to_directed()

def update_bottleneck_edges(network, nodes):
    for (u, v, data) in network.edges(data=True):
        if v in nodes and u not in nodes:
            network.edges[u, v]['packet_loss'] = 0.1

def write_graph(network):
    updated_model_path = "updated.gml"
    print(f"Writing new graph to {updated_model_path}")
    nx.readwrite.gml.write_gml(network, updated_model_path)

if __name__ == "__main__":
    opts, args = getopt.gnu_getopt(sys.argv[1:], "h", [
        "help",
    ])
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
    network_model_path = args[0]
    print(f"Using model at {network_model_path}")

    network = read_graph(network_model_path)
    bottleneck_nodes = find_nodes(network, 'CN')
    network = make_directed(network)
    update_bottleneck_edges(network, bottleneck_nodes)
    write_graph(network)
