from opcua import Client

# Replace with your OPC UA server IP address
ip_address = "opc.tcp://172.21.10.1:4840"

# Connect to the OPC UA server
client = Client(ip_address)
client.connect()

try:
    # Get the root node
    root = client.get_root_node()

    # Function to recursively find nodes
    def find_nodes(node):
        for child in node.get_children():
            node_id = child.nodeid.to_string()
            if "xCurConvStatus" in node_id:
                print(node_id)
            find_nodes(child)

    # Start the search from the root node
    find_nodes(root)

finally:
    # Disconnect from the server
    client.disconnect()