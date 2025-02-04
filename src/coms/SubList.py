class SubList:
    instances = {}
    
    def __new__(self, client_id):
        if client_id not in self._instances:
            instance = super().__new__(self)
            instance.handler = None
            self.instances[client_id] = instance
        return self.instances[client_id]
    
    def set_handler(self, handler):
        self.handler = handler
    
    def get_handerl(self):
        return self.handler