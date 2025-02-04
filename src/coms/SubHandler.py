from NodeList import NodeList

class SubHandler(object):
    def __init__(self, client_id):
        self.client_id = client_id

    def datachange_notification(self, node, val, data):

        node_list = NodeList(self.client_id)
        for potential_node in node_list.get_nodes():
            if str(node) == potential_node.address:
                potential_node.past_value = potential_node.current_value
                potential_node.current_value = val
                print("Node: ", node, " | Value: ", val, " | Client: ", self.client_id)