import time
import code
import config

from opcua import Client, ua

class NodeList:
    _instances = {}

    def __new__(self, client_id):
        if client_id not in self._instances:
            instance = super().__new__(self)
            instance._nodes = []
            self._instances[client_id] = instance
        return self._instances[client_id]
    
    def add_node(self, node):
        self._nodes.append(node)
    
    def get_nodes(self):
        return self._nodes
    
class SubList:
    _instances = {}
    
    def __new__(self, client_id):
        if client_id not in self._instances:
            instance = super().__new__(self)
            instance.handelr = None
            self._instances[client_id] = instance
        return self._instances[client_id]
    
    def set_handler(self, handler):
        self.handler = handler
    
    def get_handerl(self):
        return self.handler

class Node():
    def __init__(self, address, client_id):
        self.address = address
        self.past_value = None
        self.current_value = None
        node_list = NodeList(client_id)
        node_list.add_node(self)

class SubHandler(object):
    def __init__(self, client_id):
        self.client_id = client_id

    def datachange_notification(self, node, val, data):

        node_list = NodeList(self.client_id)
        for potential_node in node_list.get_nodes():
            if str(node) == potential_node.address:
                potential_node.past_value = potential_node.current_value
                potential_node.current_value = val

class PLC():
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.client = Client(ip_address)
        self.node_list = NodeList(ip_address)
        self.sub_list = SubList(ip_address)

        try:
            self.client.connect()
            handler = SubHandler()
            self.sub_list.set_handler(handler)

            for node_address in config.node_dictionary[ip_address]["nodes"]:
                node = Node(node_address, ip_address)
                self.node_list.add_node(node)
                self.subscribe_nodes(node, handler)

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