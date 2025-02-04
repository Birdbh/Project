class NodeList:
    _instances = {}

    def __new__(self, client_id):
        if client_id not in self._instances:
            instance = super().__new__(self)
            instance.nodes = []
            self._instances[client_id] = instance
        return self._instances[client_id]
    
    def add_node(self, node):
        self.nodes.append(node)
    
    def get_nodes(self):
        return self.nodes