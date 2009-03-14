#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 28/7/2007
'''



import os
import bosip
from boscliutils import BatchCommand
import boscliutils
import bostypes
import glob
import os.path

get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_ifup_NETIF')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_ifdown_NETIF')

get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_bridge_up_CIDR')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_bridge_down')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_init')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_down_NETIF')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_up_NETIF_CIDR')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_route_add_CIDR_gw_IP')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_route_add_IP_by_IP')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_route_add_default_IP')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_route_del_INT')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_conf_save')
get_cli().set_privilege(privileges.NONE, privileges.NORMAL, 'bcli_net_conf_show')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_inverse_resolv')

get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_autoneg_ETHIF')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_net_force_ETHIF_ETHCONF')

get_cli().set_privilege(privileges.MANUF, privileges.CONFIGURE, 'bcli_net_conf_edit_interfaces')


   
class BiferShellEthIface(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        return ['eth0', 'eth1', 'eth2']

class BiferShellEthConf(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        return ['100baseTx-FD', '100baseTx-HD', '10baseT-FD', '10baseT-HD']

class BiferShellEthMacs(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        return get_eth_macs()

get_cli().add_type('ETHIF', BiferShellEthIface())
get_cli().add_type('ETHCONF', BiferShellEthConf())
get_cli().add_type('ETHMAC', BiferShellEthMacs())
    


def iface_up(iface):
    try:
        return  os.popen("ifconfig %s" % iface).readlines()[2].strip().split()[0] == "UP"
    except:
        return False

def get_route_table():
    routes = []
    for route in os.popen("route -n").readlines()[2:]:
        dst,gw,gm,flags,metric,ref,use,iface = route.split()
        route = {}
        route['dst'] = dst
        route['gw'] = gw
        route['gm'] = gm
        route['flags'] = flags
        route['metric'] = metric
        route['ref'] = ref
        route['use'] = use
        route['iface'] = iface
        routes.append(route)
    return routes

def get_default_routes():
    default_routes = []
    for route in get_route_table():
        if route['dst'] == '0.0.0.0':
            default_routes.append(route)
    return default_routes 

def get_net_devices():
    """Return a list of networking devices"""
    devs = [os.path.basename(d) for d in glob.glob('/sys/class/net/*')]
    return devs


def get_mac(dev_name):
    """Return the hardware address of a networking device"""
    return open("/sys/class/net/%s/address" % dev_name).read().strip()

def get_eth_macs():
    """Return a list of hardware addresses of all the networking devices of the system"""
    macs = []
    for dev in get_net_devices():
        # We only get macs for real ethernet devices, not alias
        if dev.startswith('eth') and ':' not in dev:
            macs.append(get_mac(dev))
    macs.sort()
    return macs


def bcli_net(line_words):
    """Network config functions for BOS Systems.
For the shaper network control funcions see "yas" function family.    
    """
    pass


def get_supermicro_main_macs():
    """Return a (sorted) list of motherboard macs from
    a supermicro system. (Assume that the macs begins with 00:30:48)"""
    supermicro_macs = [x for x in get_eth_macs() if x.startswith('00:30:48')]
    supermicro_macs.sort()
    return supermicro_macs

def generate_iftab():
    """Create the /etc/iftab for fix the order of the network devices.
Attention. Only work correctly in Alea systems. In this systems the motherboard giga ethernet
devices are eth0 (first GigaEthernet), eth1 (Second GigaEthernet) and eth2 is the management network 
device (allways added at a pci slot).     
    """    
    iftab_file = open("/etc/iftab", "w")
    dev_num = 0
    try:
        eth0, eth1 = get_supermicro_main_macs()
    except Exception, e:
        print "This is not a Alea system, so we don't fix the order of the nertwork devices"
        return

    # Fix orther of the mother board devices
    iftab_file.write("eth0 mac %s arp 1\n" % (eth0))
    iftab_file.write("eth1 mac %s arp 1\n" % (eth1))    
    # Process other network devices
    dev_num = 2
    for mac in [m for m in get_eth_macs() if not m in [eth0, eth1]]:
        iftab_file.write("eth%d mac %s arp 1\n" % (dev_num, mac))
        dev_num = dev_num + 1
    iftab_file.close()
    print "iftab contents:"
    BatchCommand("cat /etc/iftab")    

def generate_udev_persistent_net_rules():
    udev_rules_file = open("/etc/udev/rules.d/70-persistent-net.rules", "w")
    dev_num = 0
    try:
        eth0, eth1 = get_supermicro_main_macs()
    except Exception, e:
        print "This is not a Alea system, so we don't fix the order of the nertwork devices"
        return
    
    # Fix orther of the mother board devices
    udev_rules_file.write('\nSUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*",')
    udev_rules_file.write(' ATTR{address}=="%s", ATTR{type}=="1", KERNEL=="eth*", NAME="%s"' % (eth0, "eth0"))
    udev_rules_file.write('\nSUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*",')
    udev_rules_file.write(' ATTR{address}=="%s", ATTR{type}=="1", KERNEL=="eth*", NAME="%s"' % (eth1, "eth1"))
    
    # Process other network devices
    dev_num = 2
    for mac in [m for m in get_eth_macs() if not m in [eth0, eth1]]:
        udev_rules_file.write('\nSUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*",')
        udev_rules_file.write(' ATTR{address}=="%s", ATTR{type}=="1", KERNEL=="eth*", NAME="eth%d"' % (mac, dev_num))
        dev_num = dev_num + 1

    udev_rules_file.write('\n')        
    udev_rules_file.close()
    print "persistent-net.rules contents:"
    for l in open("/etc/udev/rules.d/70-persistent-net.rules", "r").readlines():
        print l


    
    
def bcli_net_init(line_words):
    """Init conf for fix the order of the network devices.
Attention. Only work correctly in Alea systems. In this systems the motherboard giga ethernet
devices are eth0 (first GigaEthernet), eth1 (Second GigaEthernet) and eth2 is the management network 
device (allways added at a pci slot).
    """    
    if boscliutils.distrib_majorversion() == '7.04':
        generate_iftab()
    elif boscliutils.distrib_majorversion() == '8.04':
        generate_udev_persistent_net_rules()
    else:
        print "There isn't support fix ifaces order in Bos v: '%s' " % boscliutils.distrib_majorversion()


def bcli_net_show(line_words):
    """Show general information about all network devices of the system"""
    BatchCommand("ip link show")

    
def bcli_net_show(line_words):
    """Show general information about tcp/ip network conf
    """
    BatchCommand("ifconfig")    

def bcli_net_show_NETIF(line_words):
    """Show general information about tcp/ip network conf but only for the specified device
    """
    dev = line_words[2]
    if dev not in get_net_devices():
        print "Iface %s does not exists" % dev
        return     
    BatchCommand("ifconfig %s" % dev)
    if iface_up(dev):
        print "State: UP"
    else:
        print "State: DOWN"


def bcli_net_detect_IP_duplicated_NETIF(line_words):
    """Detect if the IP is duplicated at specified network
Detect if the same IP address is use by two or more systems at the phisical network conected to <NETIF> device.
    """
    ip = line_words[2]
    dev = line_words[4]
    if dev not in get_net_devices():
        print "Unknown device: %s" % dev
        return
    ret = boscliutils.InteractiveCommand("arping -q -c 2 -w 3 -D -I %s %s" % (dev, ip)).result()   
    if ret == 0:
        print "No duplicated for ip %s at %s" % (ip, dev)
    else:
        print "Duplicate use of ip %s at %s" % (ip, dev)


def bcli_net_analize_CIDR(line_words):
    """Interpret the IP/Prefix especified and show the corresponding information
Show Ip, number of bits for network, netmask ip, broadcast addres, network address,
the number of address available, the first valid address and the last valid address.    
    """
    cidr = line_words[2]
    try:
        ip_str, prefix_str = cidr.split('/')
        ip = bosip.Ip(ip_str, int(prefix_str))
        print "%s / %d" % (ip.ip(), ip.prefix())
        print "network: %s netmask %s broadcast %s" % (ip.network(), ip.netmask(), ip.broadcast())
        print "ip min: %s ip max: %s num host: %d" % (ip.ip_min(), ip.ip_max(), ip.num_ips())
    except ValueError:
        print "'%s' is not a valid CIDR" % cidr   

def bcli_net_down_NETIF(line_words):
    """Force the network interface down.
    """
    dev = line_words[2]
    BatchCommand("ifconfig %s down" % dev)




def bcli_net_bridge_show(line_words):
    """Show compact br0 bridge info if exists.
    """
    if 'br0' in get_net_devices():
        BatchCommand("/usr/sbin/brctl show br0")
        BatchCommand("ifconfig br0")
    else:
        print "Bridge br0 does't exists."
        print "Activate br0 iface using 'net bridge up' command."
    

def bcli_net_bridge_show_detail(line_words):
    """Show detailed br0 bridge info if exists.
    """
    if 'br0' in get_net_devices():
        BatchCommand("/usr/sbin/brctl show br0")
        BatchCommand("/usr/sbin/brctl showstp br0")
        BatchCommand("/usr/sbin/brctl showmacs br0")
        BatchCommand("ifconfig br0")
    else:
        print "Bridge br0 does't exists."
        print "Activate br0 iface using 'net bridge up' command."
        
def bcli_net_bridge_down(line_words):
    """Deactivate br0 bridge and bring down eth0 and eth1.
    """
    if 'br0' in get_net_devices():
        print "Shuting down br0"
        BatchCommand("/sbin/ip link set br0 down")
        BatchCommand("/usr/sbin/brctl stp br0 off")
        BatchCommand("/usr/sbin/brctl delif br0 eth0")
        BatchCommand("/usr/sbin/brctl delif br0 eth1")
        BatchCommand("/usr/sbin/brctl delbr br0")
        print "Bridge br0 down"        
    else:
        print "No bridge to shutdown"
        
    print "Shuting down eth0"
    BatchCommand("/sbin/ip link set eth0 down")
    BatchCommand("/sbin/ip addr flush eth0")
    print "Shuting down eth1"    
    BatchCommand("/sbin/ip link set eth1 down")
    BatchCommand("/sbin/ip addr flush eth1")    
    
def bcli_net_bridge_up_CIDR(line_words):
    """Create a bridge using eth0 and eth1.
    """
    cidr = line_words[3]
    try: 
        ip,prefix = cidr.split('/')
        print "Bring up br0 bridge"
        if 'br0' in get_net_devices():
            print "Bridge br0 already exists"
            print "Please bring down bridge br0"
            return

        BatchCommand("/sbin/ip link set eth0 up")
        BatchCommand("/sbin/ip link set eth1 up")
        BatchCommand("/usr/sbin/brctl addbr br0")
        BatchCommand("/usr/sbin/brctl addif br0 eth0")
        BatchCommand("/usr/sbin/brctl addif br0 eth1")
        BatchCommand("/usr/sbin/brctl stp br0 on")
            
        info_ip = bosip.Ip(ip, int(prefix))
        BatchCommand("ifconfig %s %s netmask %s broadcast %s" % 
                           ('br0', info_ip.ip(),info_ip.netmask(),
                            info_ip.broadcast()))
        
        print "Bridge br0 configured"
        print "Use 'net bridge show' to verify the interface"
    except ValueError:
        print "'%s' is not a valid CIDR" % cidr
    
def bcli_net_up_NETIF_CIDR(line_words):
    """Brings up the interface with the given IP address and netmask.    
    """
    dev, cidr = (line_words[2], line_words[3])
    try: 
        ip,prefix = cidr.split('/')
        info_ip = bosip.Ip(ip, int(prefix))
        BatchCommand("ifconfig %s %s netmask %s broadcast %s" % 
                                       (dev, info_ip.ip(),info_ip.netmask(), info_ip.broadcast()))
    except ValueError:
        print "'%s' is not a valid CIDR" % cidr
     


def bcli_net_route_add_CIDR_gw_IP(line_words):
    """Add a net route.
    """
    cidr = line_words[3]
    try: 
        ip,prefix = cidr.split('/')
        info_ip = bosip.Ip(ip, int(prefix))
    except ValueError:
        print "'%s' is not a valid CIDR" % cidr
        return
    cidr, gw = (line_words[3], line_words[5])  
    BatchCommand("route add -net %s gw %s" % (cidr, gw))

def bcli_net_route_add_IP_by_IP(line_words):
    """Add a host route
    """
    ip, gw = (line_words[3], line_words[5])  
    BatchCommand("route add -host %s gw %s" % (ip, gw))

def bcli_net_route_add_default_IP(line_words):
    """Define the default gateway
    """
    gw = line_words[4]
    BatchCommand("route add default gw %s" % (gw))
    
def route_delete(route):    
    if route['dst'] == '0.0.0.0':
        BatchCommand("route del default gw %s" % route['gw'])
    elif route['gm'] != '255.255.255.255':
        BatchCommand("route del -net %s gw %s netmask %s" %
                                       (route['dst'],route['gw'], route['gm']))
    else:
        BatchCommand("route del -host %s gw %s" %
                                       (route['dst'],route['gw']))
    
def bcli_net_route_del_INT(line_words):
    """Delete the indicated route by ID.
Delete the route by route ID. Use "net route show" to 
see the IDs.
"""
    try:
        route_number = int(line_words[3])
        routes = get_route_table()
        if route_number not in range(1, len(routes) + 1):
            print "%d is not a valid route ID" % route_number
            print 'Use "net route show" to show the actual routes'
            return 
        route_delete(routes[route_number - 1])
    except Exception, ex:
        print str(ex)
    
def bcli_net_route_show(line_words):
    """Show actual route tables.
Show info for all the ip routes registered in the system. For each route it
show ID, Destination, Gateway, Netmask, and the interface 
used. The IP 0.0.0.0 means all the possibles addresses. The ID is used for
 "net route del" command.

Use "net route show details" for more detailed output.
"""
    num = 1
    print "Routing table"
    print " ID  Destination      Gateway          Netmask          Iface"
    for route in get_route_table():
        print "[%2d] %-16s %-16s %-16s %s" % \
            (num, route['dst'], route['gw'], route['gm'], route['iface'])
        num = num + 1
        
def bcli_net_route_show_details(line_words):
    """Show actual route tables. (With more detail)
Show info for all the ip routes registered in the system. For each route it
show Destination, Gateway, Netmask, Flags, Route Metric and the interface 
used. The IP 0.0.0.0 means all the possibles addresses.
The ID is used for "net route del" command.
    """
    lines = os.popen("route -n").readlines()
    print "  ID %s" % lines[1].strip()
    num = 1
    for line in lines[2:]:
        print "[%2d] %s" % (num, line.strip())
        num = num + 1


def generate_iface_conf(if_name, out_stream):
    """Return a list of lines with the configuration corresponding to the interface 
    """
    data_line = ""
    for line in os.popen("ip addr show %s\n" % if_name).readlines()[2:]:
        if line.strip().endswith(if_name):
            data_line = line.strip()
            break
        
    data_line = data_line.strip()
    # If the device have no conf, only return
    if data_line == "": return []

    out_stream.write("# Generated Conf for %s\n" % if_name)
    out_stream.write("auto %s\n" % if_name)
    out_stream.write("iface %s inet static\n" % if_name)

    
    cidr = data_line.split()[1]
    ip_str, prefix_str = cidr.split('/')
    ip = bosip.Ip(ip_str, int(prefix_str))
    
    # Include basic ip address information
    out_stream.write("\taddress %s\n" % ip_str)
    out_stream.write("\tnetmask %s\n" % ip.netmask())
    out_stream.write("\tnetwork %s\n" % ip.network())
    out_stream.write("\tbroadcast %s\n" % ip.broadcast())

    # Include additional conf for bridges
    if if_name == 'br0':
        out_stream.write("\tpre-up /sbin/ip link set eth0 up\n")
        out_stream.write("\tpre-up /sbin/ip link set eth1 up\n")
        out_stream.write("\tpre-up /usr/sbin/brctl addbr br0\n")
        out_stream.write("\tpre-up /usr/sbin/brctl addif br0 eth0\n")
        out_stream.write("\tpre-up /usr/sbin/brctl addif br0 eth1\n")
        out_stream.write("\tup /usr/sbin/brctl stp br0 on\n")
        out_stream.write("\n")    
        out_stream.write("\tpre-down /usr/sbin/brctl stp br0 off\n")
        out_stream.write("\tpre-down /usr/sbin/brctl delif br0 eth0\n")
        out_stream.write("\tpre-down /sbin/ip link set eth0 down\n")
        out_stream.write("\tpre-down /sbin/ip addr flush eth0\n")
        out_stream.write("\tpre-down /usr/sbin/brctl delif br0 eth1\n")
        out_stream.write("\tpre-down /sbin/ip link set eth1 down\n")
        out_stream.write("\tpre-down /sbin/ip addr flush eth1\n")
        out_stream.write("\tpost-down /usr/sbin/brctl delbr br0\n")
    
    # add routing info
    # 1- Select the corresponding routes for this iface that use a GW
    iface_routes = []
    for route in get_route_table():
        if bosip.Ip(route['gw']).network() == bosip.Ip(ip_str).network():
            if route['gw'] != '0.0.0.0':
                if 'H' in route['flags']:
                    # Host route
                    out_stream.write("\tup route add -host %s gw %s\n" % (route['dst'], route['gw']))
                elif route['dst'] == '0.0.0.0':
                    # default gw
                    out_stream.write("\tup route add default gw %s\n" % (route['gw']))
                else:
                    # Network route 
                    out_stream.write("\tup route add -net %s netmask %s gw %s\n" % (route['dst'], route['gm'], route['gw']))

def get_net_ifaces():
    ifaces = []
    for l in os.popen("ifconfig").readlines():
        if l != '\n'  and l[0] != ' ':
            ifaces.append(l.split()[0])
    return ifaces

def generate_ifaces_conf_file(out_stream):
    ifaces = get_net_ifaces()
    ifaces.sort()
    
    # We generate a new interfaces file
    out_stream.write("# BosCli autogenerated\n")
    out_stream.write("# DON'T EDIT\n")
    out_stream.write("\n")
    
    out_stream.write("# Generated Conf for lo\n")
    out_stream.write("auto lo\n")
    out_stream.write("iface lo inet loopback\n")
    out_stream.write("\n")

    if 'br0' in ifaces:
        ifaces = [dev for dev in ifaces if dev not in ('eth0', 'eth1')]
        
    for iface in ifaces:
        if iface_up(iface):
            if iface.startswith('eth') or iface == 'br0':
                out_stream.write("\n")
                generate_iface_conf(iface, out_stream)


def generate_inverse_resolv():
    final_lines = []
    initial_lines = open("/etc/hosts","r").readlines()
    for l in initial_lines:
        m = re.search(r"-ip-\d*-inv-resolv", l)
        if m == None and l != "# Begin Automatic section DO NOT EDIT\n" and l != "# End Automatic section\n":
            # This line is not from inv-resolv generator
            # so we add directily to the final_lines
            final_lines.append(l)

    final_lines.append("\n")
    final_lines.append("# Begin Automatic section DO NOT EDIT\n")

    ifaces = get_net_devices()
    ifaces.sort()

    for iface in ifaces:
        lines = os.popen("ip -f inet addr show %s" % iface).readlines()
        if len(lines) >= 2:
            # We can have various alias.... in this case the cmd ouput is
            # like:
            # 2: eth0: <BROADCAST,MULTICAST,UP,10000> mtu 1500 qdisc pfifo_fast qlen 1000
            #    inet 192.168.10.237/24 brd 192.168.10.255 scope global eth0
            #    inet 192.168.5.233/24 brd 192.168.5.255 scope global eth0:0
            cont = 1
            for l in lines[1:]:
                ip = l.split()[1].split('/')[0]
                if iface == 'lo': continue
                final_lines.append("%s %s-ip-%d-inv-resolv\n" % (ip, iface, cont))
                cont = cont + 1

    final_lines.append("# End Automatic section\n")
    final_lines.append("\n")

    fd = open("/etc/hosts","w")
    fd.writelines(final_lines)
    fd.close()


def bcli_net_inverse_resolv(line_words):
    """Generate hosts conf for inverse resolv of all configured interfaces.
    """
    print "Regenerating hosts file (for inverse resolv)"
    generate_inverse_resolv()

    
def bcli_net_conf_save(line_words):
    """Save the current running net conf
    """
    if not get_cli().confirm("Are you sure"):
        print "Command canceled"
        return
        
    print "Creating confs files..."
    print "Saving hardware addresses"
    bcli_net_init([])
    print "Saving interfaces conf"

    if_file = open("/etc/network/interfaces", "w")
    generate_ifaces_conf_file(if_file)
    if_file.close()
    print "Saving ethernet conf parameters"

    ifplugd_file = open("/etc/ifplugd/action.d/ifupdown", "w")
    generate_ifplugd_action(ifplugd_file)
    ifplugd_file.close()

    print "Saving local ips at hosts file"
    generate_inverse_resolv()
    
    print "Running conf saved"
    print "Use ''net conf show'' to verify the conf"


def bcli_net_conf_show(line_words):
    """Show the actual conf files for network
    """
    print "Saved Conf ------"
    print "================="
    print "MAC Conf --------"
    if boscliutils.distrib_majorversion() == '7.04':
        print "iftab contents:"        
        BatchCommand("cat /etc/iftab")
    elif boscliutils.distrib_majorversion() == '8.04':
        BatchCommand("cat /etc/udev/rules.d/70-persistent-net.rules")
    print "Ifaces Conf -----"
    BatchCommand("cat /etc/network/interfaces")
    print "Ethernet Conf ---"
    BatchCommand("cat /etc/ifplugd/action.d/ifupdown | grep ethtool")
    print "-----------------"
    print "Hosts Conf ------"
    BatchCommand("cat /etc/hosts")
    print "-----------------"

    
def bcli_net_conf_edit_interfaces(line_words):
    """Edit manualy the interfaces file
    """
    boscliutils.InteractiveCommand("nano /etc/network/interfaces")

def bcli_net_ifup_NETIF(line_words):
    """Brings Up the iface using the interfaces conf file
    """
    dev = line_words[2]
    BatchCommand("ifup %s" % dev)

def bcli_net_ifdown_NETIF(line_words):
    """Brings Down the iface using the interfaces conf file
    """
    dev = line_words[2]
    BatchCommand("ifdown %s" % dev)


def bcli_net_force_ETHIF_ETHCONF(line_words):
    """ Change ethernet device parameters (autonegociaton, speed, etc.).
    """
    iface = line_words[2]
    media = line_words[3]

    if media not in BiferShellEthConf().values(''):
        print '%s is not a valid conf' % media
        return
    
    if media.endswith('FD'): duplex = 'full'
    else: duplex = 'half'
    if media.startswith('100'): speed = '100'
    else: speed = '10'

    BatchCommand("ethtool -s %s autoneg %s speed %s duplex %s" %
                 (iface, 'off', speed, duplex))
    BatchCommand("mii-tool %s" % (iface))
    print "Autoneg Off"

def bcli_net_autoneg_ETHIF(line_words):
    """ Change ethernet device parameters (autonegociaton, speed, etc.).
    """
    iface = line_words[2]
    BatchCommand("ethtool -s %s autoneg on" % (iface))
    print "Autoneg for %s On " % iface
    


def eth_status(iface):
    status = {
        'Speed': 'Unknown',
        'Duplex': 'Unknown',
        'Auto-negotiation': 'Unknown',
        'Link detected': 'Unknown'
        }

    for l in os.popen("ethtool %s" % (iface)).readlines():
        l = l.strip()
        try:
            key, value = l.split(':')
            if key in ['Speed', 'Duplex', 'Auto-negotiation', 'Link detected']:
                status[key] = value.strip()
        except:
            pass
    return status

def eth_status_str(iface):
    status = eth_status(iface)
    return "%s, Duplex: %s, Auto: %s, Link: %s" % (status['Speed'],
                                                   status['Duplex'],
                                                   status['Auto-negotiation'],
                                                   status['Link detected'])
    
    
def bcli_net_show_etherconf_ETHIF(line_words):
    """ Display ethernet card settings (speed, negotiation, link, ...).
    Use net etherconf to change interface parameters.
    """
    iface = line_words[3]
    if iface not in BiferShellEthIface().values(''):
        print "%s is not a valid ethernet device" % iface
    else:
        print "%s %s" % (iface, eth_status_str(iface))
    
def bcli_net_show_etherconf_ETHIF_detail(line_words):
    """ Display ethernet card settings (speed, negotiation, link, ...). Detailed version.
    Use net etherconf to change interface parameters.
    """
    iface = line_words[3]
    if iface not in BiferShellEthIface().values(''):
        print "%s is not a valid ethernet device" % iface
    else:
        BatchCommand("ethtool %s" % iface)

def bcli_net_show_etherconf(line_words):
    """ Display all ethernet card settings (speed, negotiation, link, ...).
    """
    devs = [d for d in get_net_devices() if d.startswith('eth')]
    devs.sort()
    for d in devs:
        print "%s %s" % (d, eth_status_str(d))
    

def get_etherconf(dev):
    """Return a map with the values of speed, duplex and negociation
    """
    etherconf = {}
    autoneg = True
    for l in os.popen("ethtool %s" % (dev)).readlines():
        l = l.strip()
        if l.startswith("Advertised auto-negotiation"):
            if l.split(':')[1].strip() == "No":
                autoneg = False
                break
    # At this point we are sure if the device have the negotiation
    # activated or not
    if autoneg: etherconf['autoneg'] = 'on'
    else: etherconf['autoneg'] = 'off'
    
    # We only get the speed and duplex values if the autoneg is off
    if not autoneg:
        conf = os.popen("mii-tool %s" % (dev)).readlines()
        # When forced the output of mii-tool is like
        # eth0: 100 Mbit, full duplex, link ok
        # eth1: 10 Mbit, full duplex, no link
        # eth2: 10 Mbit, half duplex, no link
        etherconf['speed'] = conf[1]
        etherconf['duplex'] = conf[3]

    return etherconf


def generate_ifplugd_action(out_stream):
    out_stream.write("#!/bin/sh\nset -e\n\n")
    out_stream.write('case "$2" in\nup)\n\t/sbin/ifup $1\n')
    for dev in get_net_devices():
        # We only need to specify conf for real ethernet devices,
        # not alias
        if dev.startswith('eth') and ':' not in dev:
            conf = get_etherconf(dev)
            if conf['autoneg'] == 'off':
                # We only fix the conf if the mode is not auto
                out_stream.write("\t/usr/sbin/ethtool -s %s " % dev)
                out_stream.write("autoneg off ")
                out_stream.write("speed %s " % conf['speed'])
                out_stream.write("duplex %s " % conf['duplex'])
                out_stream.write("\n")
    out_stream.write('\t;;\ndown)\n\t/sbin/ifdown $1\n\t;;\nesac\n')

def check_host(host):
    try:
        packets, rtt = os.popen('ping -c 5 -q -w 5 %s 2>/dev/null' % host).readlines()[-2:]
        send = int(packets.split()[0])
        recv = int(packets.split()[3])
        loss = int(packets.split()[5][:-1])
        min,avg,max,mdev = map(float, rtt.split()[3].split('/'))
        if loss >= 15 or avg >= (100):
            return False
        else:
            return True
    except:
        return False

def print_connection(host):
    if check_host(host):
        status = "OK"
    else:
        status = "ERROR"
    print "%-10s host %-40s" % (status, host)
    
def bcli_check_net_resolv(line_words):
    """Check for connection problems with nameservers configured"""
    print "Check resolv.conf hosts"
    for l in open('/etc/resolv.conf').readlines():
        l = l.strip()
        if l.startswith('nameserver'):
            print_connection(l.split()[1])
                
def bcli_check_net(line_words):
    """Check for connection problems (using some preconfigured hosts)"""
    without_dns = ['212.230.0.49', '212.230.0.50']
    with_dns = ['www.google.com', 'www.alea-soluciones.com']
    
    print "Check host (without using DNS)"
    for h in without_dns:
        print_connection(h)
    print "Check host (using DNS)"
    for h in with_dns:
        print_connection(h)


def bcli_net_show_open_tcp_connections(line_words):
    """Show TCP connections
    """
    BatchCommand("netstat -nt")

def bcli_net_show_open_udp_connections(line_words):
    """Show UDP connections
    """
    BatchCommand("netstat -nu")

def bcli_net_show_open_connections(line_words):
    """Show TCP/UDP connections
    """
    BatchCommand("netstat -nut")

def bcli_net_show_listen_ports(line_words):
    """Show TCP/UDP open port (listen mode)
    """
    BatchCommand("netstat -ntul")
    
def bcli_net_show_listen_udp_ports(line_words):
    """Show UDP open port (listen mode)
    """
    BatchCommand("netstat -nul")
    
def bcli_net_show_listen_tcp_ports(line_words):
    """Show TCP open port (listen mode)
    """
    BatchCommand("netstat -ntl")

