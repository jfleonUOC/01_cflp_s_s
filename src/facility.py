"""

"""


class Facility():
    """
    Class for handling facilities
    """
    def __init__(self, id: str, capacity: float, cost_open: float):
        self.id = id
        self.capacity = capacity
        self.cost_open = cost_open
        # self.is_open = True
        # self.served_clients = []

        self.message_on_creation()
    
    def __str__(self) -> str:
        return f"Facility {self.id}"

    def __repr__(self) -> str:
        return f"Facility {self.id}"

    def message_on_creation(self):
        """
        Message on creation
        TODO: add verbose option to disable message
        """
        print(f"Facility {self.id} - capacity: {self.capacity}; cost: {self.cost_open}")