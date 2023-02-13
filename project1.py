from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ether_types
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
from pprint import pprint
import json
import time
import sdn_info_request as sdninfo
from pprint import pprint

MASTER_IP = "192.168.2.17"
MASTER_PORT = "6000"


class Kruskal(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Kruskal, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.swdpid = {}
        self.hstmac = {}
        self.swport = {}
        self.Node = dict()
        self.Rank = dict()
        self.nodelist = Kruskal.kruskal(self)
        self.swdpid1 = sdninfo.get_switch_dpid("group8", "project1")
        #flag变量标志到达交换机的数据包是发送包或者返回包，初始化为零
        self.flag = {}
        for sch in self.swdpid1.keys():
            hexstr = self.swdpid1[sch][4:]
            self.swdpid1[sch] = int(hexstr, 16)
        for i in range(len(self.nodelist)-2):
            self.flag[self.swdpid1[self.nodelist[i+1]]] = 0

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        print("table miss")
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        print("addflow doing!")
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(event.EventSwitchEnter, [CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def switch_enter_handler(self, ev):
        #time.sleep(self.sleep_interval)
        print("A switch entered.\n------------------------------")

    def kruskal(self):
        with open("project1_test.json", "r") as f:
            topo_dict = json.load(f)
        dict_links = topo_dict.get('networks').get('links')
        a = list(dict_links.keys())
        edges = []
        for i in range(len(a)):
            tup = (dict_links.get(a[i]).get('config').get('source').get('delay_us'), dict_links.get(a[i]).get('source'),
                   dict_links.get(a[i]).get('target'))
            edges.append(tup)
        nodes = list(topo_dict.get('networks').get('hosts').keys())
        dict_nodes = topo_dict.get('networks').get('switches')
        switch = list(dict_nodes.keys())
        for i in range(len(switch)):
            nodes.append(switch[i])

        minitree = Kruskal.Kruskal_1(self, nodes, edges)
        pprint("the MST is:\n")
        print(minitree)
        edge_list = list()
        dict_STP = dict()
        for i in range(len(nodes)):
            for j in range(len(minitree)):
                if nodes[i] == minitree[j][1]:
                    edge_list.append(minitree[j][1] + minitree[j][2])
                    dict_STP[nodes[i]] = edge_list
                elif nodes[i] == minitree[j][2]:
                    edge_list.append(minitree[j][2] + minitree[j][1])
                    dict_STP[nodes[i]] = edge_list
            edge_list = list()

        edge_list = list()
        dict_node = dict()
        for i in range(len(nodes)):
            for j in range(len(minitree)):
                if nodes[i] == minitree[j][1]:
                    edge_list.append(minitree[j][2])
                    dict_node[nodes[i]] = edge_list
                elif nodes[i] == minitree[j][2]:
                    edge_list.append(minitree[j][1])
                    dict_node[nodes[i]] = edge_list
            edge_list = list()

        head = input('host1\n')
        rare = input('host2\n')
        path = []
        paths = []
        nodelist = Kruskal.findPath(self, dict_node, head, rare, path, paths)[0]
        print('the path from', head, 'to', rare, 'is:')
        pprint(nodelist)
        pathlist = list()
        for i in range(len(nodelist) - 1):
            pathlist.append(nodelist[i] + nodelist[i + 1])
        #print('###the path is###')
        #pprint(pathlist)
        #print('###time is###')
        delaytime = 0
        for i in range(len(nodelist) - 1):
            for j in range(len(minitree)):
                if (nodelist[i] == minitree[j][1] or nodelist[i] == minitree[j][2]) and (
                        nodelist[i + 1] == minitree[j][1] or nodelist[i + 1] == minitree[j][2]):
                    t = int(minitree[j][0])
                    delaytime = delaytime + t
        #print((delaytime / 1000) * 2, end='ms\n')
        return nodelist

    def findPath(self, dict_node, start, end, path, paths):
        path = path + [start]
        if start == end:
            return path
        for node in dict_node[start]:
            if node not in path:
                newnodes = Kruskal.findPath(self, dict_node, node, end, path, paths)
                for newnode in newnodes:
                    if newnode == end:
                        path.append(newnode)
                        paths.append(path)
        return paths

    def Nodeinit(self, node):
        self.Node[node] = node
        self.Rank[node] = 0

    def Find_rt(self, node):
        if self.Node[node] != node:
            self.Node[node] = Kruskal.Find_rt(self, self.Node[node])
        return self.Node[node]

    def Union(self, node1, node2):
        rt1 = Kruskal.Find_rt(self, node1)
        rt2 = Kruskal.Find_rt(self, node2)
        if self.Rank[rt1] > self.Rank[rt2]:
            self.Node[rt2] = Kruskal.Find_rt(self,rt1)
        else:
            self.Node[rt1] = Kruskal.Find_rt(self, rt2)
            if self.Rank[rt1] == self.Rank[rt2]:
                self.Rank[rt2] += 1

    def Kruskal_1(self, nodes, edges):
        for i in range(len(nodes)):
            Kruskal.Nodeinit(self, nodes[i])
        minitree = []
        edges.sort(reverse=False)
        for i in range(len(edges)):
            if Kruskal.Find_rt(self, edges[i][1]) != Kruskal.Find_rt(self, edges[i][2]):
                Kruskal.Union(self, edges[i][1], edges[i][2])
                minitree.append(edges[i])
        return minitree

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id

        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        arp_pkt = pkt.get_protocol(arp.arp)

        dst_mac = eth_pkt.dst
        src_mac = eth_pkt.src
        in_port = msg.match['in_port']
        out_port = None

        Is_arp = 0

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        if eth.ethertype == 38:
            return
        if arp_pkt:
            Is_arp = 1
            print("arp received~")

        nodelist = self.nodelist
        #nodelist是所求的两点之间的路径
        swdpid = sdninfo.get_switch_dpid("group8", "project1")
        #对获得的16进制dpid转换为10进制
        for sch in swdpid.keys():
            hexstr = swdpid[sch][4:]
            swdpid[sch] = int(hexstr, 16)
        swport = sdninfo.get_switch_port("group8", "project1")
        hstmac = sdninfo.get_host_mac("group8", "project1")
        dpidsw = {}
        #flag为零则说明是发送的包，flag为1则是是返回的包
        if self.flag[dpid]:
            dst_mac = hstmac[nodelist[0]]
            src_mac = hstmac[nodelist[len(nodelist) - 1]]
        else:
            src_mac = hstmac[nodelist[0]]
            dst_mac = hstmac[nodelist[len(nodelist) - 1]]
        self.flag[dpid] = self.flag[dpid]+1

        #交换机名称在后，dpid在前
        for sw in swdpid.keys():
            dpidsw[swdpid[sw]] = sw
        #获得当前交换机名称
        swnow = dpidsw[dpid]
        for i in range(len(nodelist) - 1):
            if nodelist[i] == swnow:
                for strs in swport[swnow]:
                #构建s1s2之类的两点确定的边，便于匹配端口
                    if self.flag[dpid] == 1:
                        if strs == nodelist[i] + nodelist[i + 1]:
                            out_port = swport[swnow][strs]
                    elif self.flag[dpid] == 2:
                        if strs == nodelist[i] + nodelist[i-1]:
                            out_port = swport[swnow][strs]

        if out_port is None:
            print("out_port fail")
            return
        else:
            out_port = int(out_port)

        if self.flag[dpid] < 3:
            actions = [parser.OFPActionOutput(out_port)]
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst_mac)
            #flag为1说明发送包，优先值为1，flag为2说明返回包，流表优先权为2
            if self.flag[dpid] == 1:
                self.add_flow(datapath, 1, match=match, actions=actions)
            else:
                self.add_flow(datapath, 2, match=match, actions=actions)
            print("flow added!\narp send!")

        # packet out
            out = parser.OFPPacketOut(datapath=datapath,
                                      buffer_id=ofproto.OFP_NO_BUFFER,
                                      in_port=in_port, actions=actions,
                                      data=msg.data)
            datapath.send_msg(out)

