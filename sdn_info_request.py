#from sdn_info_query_master import MASTER_PORT
import requests

MASTER_IP = "192.168.2.17"
MASTER_PORT = "6000"

def get_switch_dpid(user, topo):
    data = {
        "user": user,
        "topo": topo
    }
    resp = requests.post(url=f"http://{MASTER_IP}:{MASTER_PORT}/switch_dpid/",
                         json=data)
    #print(resp.json())
    return resp.json()


def get_host_mac(user, topo):
    data = {
        "user": user,
        "topo": topo
    }
    resp = requests.post(url=f"http://{MASTER_IP}:{MASTER_PORT}/host_mac/",
                         json=data)
    #print(resp.json())
    return resp.json()


def get_switch_port(user, topo):
    data = {
        "user": user,
        "topo": topo
    }
    resp = requests.post(url=f"http://{MASTER_IP}:{MASTER_PORT}/link_port/",
                         json=data)
    #print(resp.json())
    return resp.json()

if __name__ == "__main__":
    sw2dpid = get_switch_dpid("sw", "kruskal_test")
    host2mac = get_host_mac("sw", "kruskal_test")
    sw2port = get_switch_port("sw", "kruskal_test")