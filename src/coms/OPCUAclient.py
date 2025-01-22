import time
import code

from opcua import Client, ua

IP_ADDRESS ="opc.tcp://172.21.3.1:4840"
NS_NUMBER = 3
global client

class NodeList:
    _instance = None
    _nodes = [] 
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def add_node(cls, node):
        cls._nodes.append(node)
    
    @classmethod
    def get_nodes(cls):
        return cls._nodes

class Node():
    def __init__(self, datablock, tag_name):
        self.ns_number = NS_NUMBER
        self.datablock = datablock
        self.tag_name = tag_name
        self.address = 'ns=' + str(self.ns_number) + ';s="' + self.datablock + '"."' + self.tag_name + '"'
        self.past_value = False
        self.current_value = False
        self.rising_edge = False
        NodeList.add_node(self)

    def update_rising_edge(self):
        if self.past_value is False and self.current_value is True:
            self.rising_edge = True
            print("Rising edge detected")
        else:
            self.rising_edge = False

    def write(self, value):
        try:
            node = client.get_node(self.address)  # Access the global client variable
            node.set_value(ua.DataValue(ua.Variant(value, node.get_data_type_as_variant_type())))
        except Exception as e:
            print(e)

class SubHandler(object):
    def datachange_notification(self, node, val, data):

        for potential_node in NodeList.get_nodes():
            if str(node) == potential_node.address:
                potential_node.past_value = potential_node.current_value
                potential_node.current_value = val
                potential_node.update_rising_edge()

class PLC_COM():
    def __init__(self):
        global client
        client = Client(IP_ADDRESS)

        try:
            client.connect()
            handler = SubHandler()

            for node in NodeList.get_nodes():
                self.subscribe_nodes(node, handler)

        except Exception as e:
            print(e)

    def subscribe_nodes(self, node, handler):
        node_address = node.address
        sub = client.create_subscription(500, handler)
        variable = client.get_node(node_address)
        handle = sub.subscribe_data_change(variable)