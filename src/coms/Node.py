from NodeList import NodeList

class Node():
    def __init__(self, address, client_id):
        self.address = address
        self.past_value = None
        self.current_value = None
        node_list = NodeList(client_id)
        node_list.add_node(self)