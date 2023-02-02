"""
"""

from facility import Facility
from client import Client
import pandas as pd

class Importer():
    """
    Class to handle bechmark data import
    """
    def __init__(self,import_file_path):
        self.import_file_path = import_file_path

        self.facilities = []
        self.clients = []
        self.cost_matrix = pd.DataFrame()

        self.fac_dict = dict()
        self.cli_dict = dict()

        self.status = False

        self.import_file()
    
    def import_file(self):
        """
        Import data from the given path
        Returns as class properties the:
        1. facilities (list)
        2. clientes (list)
        3. cost matrix (data frame)
        """
        print(20*"*")
        with open(self.import_file_path, "r") as file:
            print(f"reading: {self.import_file_path}")
            # read block 1: number of facilities and clients 
            block_1 = file.readline().strip()
            number_facilities, number_clients = [int(number) for number in block_1.split()]
            print(f"number of facilities: {number_facilities}")
            print(f"number of clients: {number_clients}")
            # read block 2: facilities capacities and open costs
            for id in range(1, number_facilities+1):
                sub_block_2 = file.readline().strip()
                capacity_i, open_cost_i = [float(number) for number in sub_block_2.split()]
                facility = Facility(id, capacity_i, open_cost_i)
                self.facilities.append(facility)
                self.fac_dict[id] = facility
            # read block 3: client demands
            n_client = 1
            while n_client < number_clients + 1:
                sub_block_3 = file.readline().strip()
                demands = [float(number) for number in sub_block_3.split()]
                for demand in demands:
                    client = Client(n_client, demand)
                    self.clients.append(client)
                    self.cli_dict[n_client] = client
                    n_client += 1
            # read block 4: client-facility costs
            for client in range(1, number_clients + 1):
                facilities = [facility for facility in range(1, number_facilities + 1)]
                sub_block_4 = file.readline().strip()
                costs = [float(number) for number in sub_block_4.split()]
                df_data = dict(zip(facilities,costs))
                client_costs = pd.DataFrame([costs], index=[client], columns=facilities)
                self.cost_matrix = pd.concat([self.cost_matrix, client_costs])
            print(f"cost matrix created: {self.cost_matrix.shape}")
        print("importer end")
        print(20*"*")


if __name__ == "__main__":
    file_path = "inputs/Holmberg_Instances/p2"
    data = Importer(file_path)
    # print(data.cost_matrix)
