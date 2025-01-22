from OpcuaClient import COM
from OpcuaClient import NodeList
from OpcuaClient import Node

import time
class ComsManager():
    def __init__(self):

        self.nodes = NodeList()
        self.plc = COM()