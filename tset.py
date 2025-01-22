import time
from opcua import Client, ua, Server

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

class Node:
    def __init__(self, datablock, tag_name, ns_number):
        self.ns_number = ns_number
        self.datablock = datablock
        self.tag_name = tag_name
        self.address = f'ns={self.ns_number};s="{self.datablock}"."{self.tag_name}"'
        self.past_value = False
        self.current_value = False
        self.rising_edge = False
        NodeList.add_node(self)

    def update_rising_edge(self):
        if self.past_value is False and self.current_value is True:
            self.rising_edge = True
            print(f"Rising edge detected for {self.datablock}.{self.tag_name}")
        else:
            self.rising_edge = False

class SubHandler:
    def __init__(self, nodes):
        self.nodes = nodes

    def datachange_notification(self, node, val, data):
        for potential_node in self.nodes:
            if str(node) == potential_node.address:
                potential_node.past_value = potential_node.current_value
                potential_node.current_value = val
                potential_node.update_rising_edge()

class PLC_COM:
    def __init__(self, ip_address, ns_number):
        self.client = Client(ip_address)
        self.ns_number = ns_number
        self.subscription = None
        self.handler = None
        self.nodes = []
        try:
            self.client.connect()
            self.nodes = [node for node in NodeList.get_nodes() if node.ns_number == self.ns_number]
            self.handler = SubHandler(self.nodes)
            self.subscription = self.client.create_subscription(500, self.handler)
            for node in self.nodes:
                variable = self.client.get_node(node.address)
                self.subscription.subscribe_data_change(variable)
        except Exception as e:
            print(f"Connection error: {e}")

    def write(self, node, value):
        try:
            variable = self.client.get_node(node.address)
            dtype = variable.get_data_type_as_variant_type()
            variant = ua.Variant(value, dtype)
            dv = ua.DataValue(variant)
            variable.set_value(dv)
        except Exception as e:
            print(f"Write error: {e}")

    def disconnect(self):
        self.client.disconnect()

def test_multiple_clients():
    # Setup OPCUA server
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("Test Server")

    # Register namespaces
    ns1 = server.register_namespace("NS1")
    ns2 = server.register_namespace("NS2")

    # Create nodes in different namespaces
    objects = server.get_objects_node()
    folder1 = objects.add_folder(ns1, "TestFolder1")
    folder2 = objects.add_folder(ns2, "TestFolder2")

    var1 = folder1.add_variable(ns1, "TestVar1", False)
    var2 = folder2.add_variable(ns2, "TestVar2", False)
    var1.set_writable()
    var2.set_writable()

    # Start server
    server.start()
    print("Server started at opc.tcp://0.0.0.0:4840")

    try:
        # Create nodes for clients
        node1 = Node("TestFolder1", "TestVar1", ns1)
        node2 = Node("TestFolder2", "TestVar2", ns2)

        # Create clients
        plc_com1 = PLC_COM("opc.tcp://localhost:4840/freeopcua/server/", ns1)
        plc_com2 = PLC_COM("opc.tcp://localhost:4840/freeopcua/server/", ns2)

        # Test rising edge detection
        plc_com1.write(node1, True)
        time.sleep(1)
        assert node1.rising_edge, "Rising edge not detected for node1"

        plc_com2.write(node2, True)
        time.sleep(1)
        assert node2.rising_edge, "Rising edge not detected for node2"

        # Test rising edge after reset
        plc_com1.write(node1, False)
        time.sleep(0.5)
        plc_com1.write(node1, True)
        time.sleep(1)
        assert node1.rising_edge, "Rising edge should be detected again for node1"

        print("All tests passed!")

    finally:
        server.stop()

if __name__ == "__main__":
    test_multiple_clients()