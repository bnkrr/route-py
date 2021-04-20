# binary route table
import struct
import socket

def bin_iter(i, start_bit, end_bit):
    while start_bit > end_bit:
        start_bit -= 1
        yield (i >> start_bit) & 1

def ip2int(ip_str):
    return struct.unpack('!I', socket.inet_aton(ip_str))[0]

def ip6int(ip6_str):
    high64, low64 = struct.unpack('!QQ', socket.inet_pton(socket.AF_INET6, ip6_str))
    return (high64 << 64) + low64

def get_natural_netmask(ip_int):
    high8 = (ip_int >> 24) & 255
    if     1 <= high8 < 127:
        return 8
    elif 128 <= high8 < 192:
        return 16
    elif 192 <= high8 < 224:
        return 24
    else:
        return 32

def network2int(ip_network):
    info = ip_network.split('/')
    ip_int = ip2int(info[0])
    if len(info) == 2:
        prefix_len = int(info[1])
    else:
        prefix_len = get_natural_netmask(ip_int)
    return ip_int, prefix_len

def ipv4_bin_iter(ip_network, isNetwork=False):
    ip_int, prefix_len = network2int(ip_network)
    if not isNetwork:
        prefix_len = 32
    return bin_iter(ip_int, 32, 32-prefix_len)

def ipv4_bin_iter_l(ip_network, isNetwork=False):
    ip_int, prefix_len = network2int(ip_network)
    if not isNetwork:
        prefix_len = 32
    print(prefix_len)
    return bin_iter(ip_int, 32, 32-prefix_len)


def network6int(ip_network):
    info = ip_network.split('/')
    ip_int = ip6int(info[0])
    if len(info) == 2:
        prefix_len = int(info[1])
    else:
        prefix_len = 64
    return ip_int, prefix_len

def ipv6_bin_iter(ip_network, isNetwork=False):
    ip_int, prefix_len = network6int(ip_network)
    if not isNetwork:
        prefix_len = 128
    return bin_iter(ip_int, 128, 128-prefix_len)


class RouteNode(object):
    def __init__(self, indexes=None):
        if indexes is None:
            self.indexes = []
        else:
            self.indexes = indexes
        self.children = [None, None]

class BinaryRouteTable(object):
    def __init__(self, version=4):
        self.root = RouteNode()
        if version == 4:
            self.ip_bin_iter = ipv4_bin_iter
        else:
            self.ip_bin_iter = ipv6_bin_iter

    def add(self, ip_network, index):
        node = self.root
        for b in self.ip_bin_iter(ip_network, isNetwork=True):
            if node.children[b] is None:
                node.children[b] = RouteNode()
            node = node.children[b]
        node.indexes.append(index)

    def lookup(self, ip):
        node = self.root
        indexes = []
        for b in self.ip_bin_iter(ip, isNetwork=False):
            if node.indexes:
                indexes = node.indexes
            if node.children[b] is None:
                return indexes
            node = node.children[b]
        return indexes # just in case
    
    def lookup_len(self, ip):
        node = self.root
        indexes = []
        l = 0
        for b in self.ip_bin_iter(ip, isNetwork=False):
            if node.indexes:
                indexes = node.indexes
            if node.children[b] is None:
                return l, indexes
            node = node.children[b]
            l += 1
        return l, indexes # just in case

class ExtendRouteTable(BinaryRouteTable):
    def __init__(self, version=4):
        super().__init__(version)
        self._entries = []

    def add(self, ip_network, entry):
        self._entries.append(entry)
        index = len(self._entries) - 1
        return super().add(ip_network, index)

    def lookup(self, ip, isNetwork=False):
        indexes = super().lookup(ip)
        return [self._entries[ix] for ix in indexes]

    def lookup_len(self, ip, isNetwork=False):
        l, indexes = super().lookup_len(ip)
        return l, [self._entries[ix] for ix in indexes]



def build_rt(rt_path, ip_version): 
    rt = ExtendRouteTable(ip_version)
    with open(rt_path, 'r') as f:
        next(f)
        next(f)  # skip header
        for line in f:
            route = line.split('|')
            rt.add(route[1], route[6])
    return rt


if __name__ == '__main__':
    rt = build_rt('/path/to/route_table', 4)
    asp = rt.lookup('1.1.1.0/24', isNetwork=True)
    print(asp)


