"""

"""

class Client:
    """
    Class for handling clients
    """
    def __init__(self, id, demand):
        self.id = id
        self.demand = demand
        self.is_active = True

        self.message_on_create()

    def __str__(self) -> str:
        return f"Client {self.id}"

    def __repr__(self) -> str:
        return f"Client {self.id}"

    def message_on_create(self):
        print(f"Client {self.id} - demand: {self.demand}")