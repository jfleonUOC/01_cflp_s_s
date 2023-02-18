"""
"""

from facility import Facility
from client import Client
import os
import sys
import pandas as pd

class Importer():
    """
    Class to handle bechmark data import
    """
    def __init__(self,import_file_path=""):
        self.import_file_path = import_file_path

        self.facilities = []
        self.clients = []
        self.cost_matrix = pd.DataFrame()
        self.marginal_cost_matrix = pd.DataFrame()

        self.fac_dict = dict()
        self.cli_dict = dict()

        self.status = False

        if self.import_file_path == "":
            self.import_file_path = self.instance_selector()
        self.instance_type = self.import_file_path.split("/")[1]
        self.import_file()
        self.calculate_marginal_cost()
    
    def get_input(self, values, question):
        """
        ask input from user
        the user can select values from a given list
        the user can escape typing 'quit'
        """
        values_dict = {}
        output = ""
        for option, value in enumerate(values, start=1):
            print(f"{option}: {value}")
            values_dict[option] = value
        quit = False
        while not quit:
            selection = input(question)
            if selection == "quit":
                quit = True
                break
            try:
                selection = int(selection)
                if selection in values_dict.keys():
                    output = values_dict[int(selection)]
                    break
                else:
                    print("invalid input! Try again or type 'quit'.")
            except ValueError:
                print("invalid input! Try again or type 'quit'.")
        if output == "":
            sys.exit(0)
        else:
            return output

    def instance_selector(self):
        """
        terminal-based sequence to select instance type
        """
        print(20*"*")
        print("Instance selector")
        # find instances folder in input path
        root = "inputs/"
        dir_list = [item for item in os.listdir(root) if os.path.isdir(os.path.join(root,item))]
        print(20*"*")
        folder_selection = self.get_input(dir_list, "Select type of instances: ")
        print(f"> '{folder_selection}' selected")
        folder = root+folder_selection+"/"
        instance_list = [item for item in os.listdir(folder) if os.path.isfile(os.path.join(folder,item))]
        print(20*"*")
        instance_selection = self.get_input(instance_list, "Select instance: ")
        print(f"> '{instance_selection}' selected")
        self.import_file_path = folder+instance_selection
        print(self.import_file_path)
        return self.import_file_path



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
            print(f"instance type: {self.instance_type}")
            # read block 1: number of facilities and clients 
            block_1 = file.readline().strip()
            number_facilities, number_clients = [int(number) for number in block_1.split()]
            print(f"number of facilities: {number_facilities}")
            print(f"number of clients: {number_clients}")
            # read block 2: facilities capacities and open costs
            print("> parsing facilities")
            for id in range(1, number_facilities+1):
                sub_block_2 = file.readline().strip()
                capacity_i, open_cost_i = [float(number) for number in sub_block_2.split()]
                facility = Facility(id, capacity_i, open_cost_i)
                self.facilities.append(facility)
                self.fac_dict[id] = facility
            # read block 3: client demands
            print("> parsing clients")
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
            print("> creating cost matrix")
            if self.instance_type == "Holmberg_Instances":
                for client in range(1, number_clients + 1):
                    facilities = [facility for facility in range(1, number_facilities + 1)]
                    sub_block_4 = file.readline().strip()
                    costs = [float(number) for number in sub_block_4.split()]
                    if len(costs) < len(facilities):
                        sub_block_n = file.readline().strip()
                        costs.extend([float(number) for number in sub_block_n.split()])
                    client_costs = pd.DataFrame([costs], index=[client], columns=facilities)
                    self.cost_matrix = pd.concat([self.cost_matrix, client_costs])
            else:
                for facility in range(1, number_facilities + 1):
                    clients = [client for client in range(1, number_clients + 1)]
                    # facilities = [facility for facility in range(1, number_facilities + 1)]
                    sub_block_4 = file.readline().strip()
                    costs = [float(number) for number in sub_block_4.split()]
                    if len(costs) < number_clients:
                        sub_block_n = file.readline().strip()
                        costs.extend([float(number) for number in sub_block_n.split()])
                    client_costs = pd.DataFrame([costs], index=[facility], columns=clients)
                    self.cost_matrix = pd.concat([self.cost_matrix, client_costs])
                self.cost_matrix = self.cost_matrix.transpose()

            print(f"cost matrix created: {self.cost_matrix.shape}")
        print("importer end")
        print(20*"*")

    def calculate_marginal_cost(self):
        """
        calculate marginal cost matrix
        marginal cost: difference between the cost associated with facility and second best facility
        """
        print("Calculating marginal cost matrix ...")
        new_row_df_list = []
        row_indices = []
        for row_index, row in self.cost_matrix.iterrows():
            new_row = {}
            for col_index, col in row.items():
                # get minimum in row except current
                filtered_row = row[(row.index != col_index)]
                min_in_row = filtered_row.min()
                # substract current to minimum
                marginal_cost = min_in_row - col
                new_row[col_index] = [marginal_cost]
            new_row_df = pd.DataFrame.from_dict(new_row)
            new_row_df_list.append(new_row_df)
            row_indices.append(row_index)
        self.marginal_cost_matrix = pd.concat(new_row_df_list, ignore_index=True)
        self.marginal_cost_matrix.index = row_indices
        # print(self.marginal_cost_matrix)
        print("marginal cost matrix created")
        print(20*"*")

if __name__ == "__main__":
    # folder = "Holmberg_Instances/"
    # folder = "OR-Library_Instances/"
    folder = "Yang_Instances/"
    subfolder = ""
    # subfolder = "30-200/"
    # instance = "p13"
    # instance = "cap61"
    instance = "30-200-1"
    file_path = "inputs/"+folder+subfolder+instance
    # data = Importer(file_path)
    data = Importer()
    # print(data.cost_matrix)
