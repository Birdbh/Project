import time
import code
import config

from opcua import Client, ua
from NodeList import NodeList
from SubList import SubList
from SubHandler import SubHandler
from Node import Node

class PLC():
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.client = Client(ip_address)
        self.node_list = NodeList(ip_address)
        self.sub_list = SubList(ip_address)

        try:
            self.client.connect()
            handler = SubHandler(self.ip_address)
            self.sub_list.set_handler(handler)

            for node_address in config.node_dictionary[ip_address]["nodes"]:
                try:
                    node = Node(node_address, ip_address)
                    self.subscribe_nodes(node, handler)

                except Exception as e:
                    print(e)

        except Exception as e:
            print(e)

    def subscribe_nodes(self, node, handler):
        node_address = node.address
        sub = self.client.create_subscription(500, handler)
        variable = self.client.get_node(node_address)
        handle = sub.subscribe_data_change(variable)

class PLC_Manager():
    def __init__(self):
        self.plcs = []
        self.node_dictionary = config.node_dictionary

    def add_plc(self, ip_address):
        plc = PLC(ip_address)
        self.plcs.append(plc)

    def add_all(self):
        for ip_address in self.node_dictionary:
            self.add_plc(ip_address)

manager = PLC_Manager()
manager.add_all()