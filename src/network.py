"""

"""

from importer import Importer
from pyvis.network import Network
import copy
import textwrap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def action_decorator(action):
    action_name = action.__name__
    # action_param = func.__code__.co_varnames[:func.__code__.co_argcount]
    def inner(*args, **kwargs):
        print(f"> action: {action_name}", end="; ")
        print(f"-> {args[1:]}")
        return action(*args, **kwargs)
    return inner

class Net:
    """
    Class for handling nets
    """
    def __init__(self, id, data:Importer):
        self.id = id
        self.data = data
        self.opened_facilities = []
        self.assigned_clients = []
        self.connection_matrix = self.data.cost_matrix.astype(int)
        self.total_cost:float = 0.0
        self.updated = True
        self.complete = False
        self.valid = False
        self.capacity = False

        self.initilize()
      
    def __str__(self) -> str:
        net_summary = f"""
        net INFO: id - {self.id}
        - complete: {self.complete}
        - valid: {self.valid}
        - capacity: {self.capacity}
        - total cost: {self.total_cost:+}
        """
        return textwrap.dedent(net_summary)

    def initilize(self):
        """
        All facilities are opened
        No customer is assigned to facilities
        """
        self.connection_matrix[:] = 0
        self.update_net(verbose=False)
        # self.opened_facilities = data.facilities
        # self.assigned_clients = []

    def update_net(self, check=True, verbose=False):
        """
        Update opened facilities and assigned clients from connection matrix
        """
        self.assigned_clients = self.get_assigned_clients()
        self.opened_facilities = self.get_open_facilities()
        if verbose:
            print("> net updated")
            print(f"facilities: {self.opened_facilities}")
            print(f"clients: {self.assigned_clients}")
        if check:
            self.complete = self.is_complete()
            self.valid = self.is_valid()
            self.capacity = self.is_capacity_ok()
        self.updated = True

    def calc_cost(self, verbose=False) -> float:
        """
        Evaluate the total cost of the net
        total_cost = fixed_cost + variable_cost
            fixed_cost = Sum(opened_facilities)
            variable_cost = Sum(assigned_clients)
        """
        # check net first
        # if not self.is_valid():
        #     self.total_cost = 0.0
        #     print("invalid net -> cost initialized to 0.0")
        #     return
        # update net
        if not self.updated:
            self.update_net(verbose)
        # initialize costs
        fixed_cost:float = 0.0
        variable_cost:float = 0.0
        self.total_cost = 0.0
        # fixed cost
        for facility in self.opened_facilities:
            fixed_cost += facility.cost_open
        # variable cost
        for client in self.assigned_clients:
            # get facility index
            fac_idx = self.connection_matrix.loc[client.id].idxmax()
            # get client-facility cost
            variable_cost += self.data.cost_matrix.loc[client.id, fac_idx]
        # total cost
        self.total_cost = fixed_cost + variable_cost
        if verbose:
            print(f"total cost of net = {self.total_cost}")
        return self.total_cost

    def is_complete(self):
        """
        check if net is complete: there are not unassigned clients
        """
        if set(self.assigned_clients) != set(self.data.clients):
            print("Incomplete net: there are unassigned clients")
            # TODO: find unassigned clients
            self.complete = False
            return False
        print("Complete net")
        self.complete = True
        return True

    def is_valid(self):
        """
        Check if the net is valid: each client is assigned to only one facility
        """
        if self.connection_matrix.values.sum() > len(self.data.clients):
            print("Invalid net: clients assigned more than once to a facility")
            # TODO: find multi-assigned clients
            # print(self.connection_matrix)
            self.valid = False
            return False
        self.valid = True
        print("Valid net")
        return True

    def is_capacity_ok(self) -> bool:
        """
        Check if capacity from facilities is not exceeded
        """
        capacity_ok = True
        for facility in self.opened_facilities:
            # calculate aggregated demand
            agg_demand = self.calc_agg_demand_facility(facility)
            # compare with facility capacity
            if facility.capacity < agg_demand:
                print(f"{facility} capacity is exceeded")
                capacity_ok = False
        if capacity_ok:
            print("Capacity not exceeded")
        self.capacity = capacity_ok
        return capacity_ok

    def check(self) -> bool:
        """
        perform complete check
        """
        if self.is_complete() and self.is_valid() and self.is_capacity_ok():
            return True
        else:
            return False

    def get_assigned_clients(self) -> list:
        """
        get assigned clients from connection matrix
        """
        list_assigned_cli = []
        list_assigned_cli_id = self.connection_matrix[self.connection_matrix.eq(1).any(axis=1)].index.tolist()
        for id in list_assigned_cli_id:
            list_assigned_cli.append(self.data.cli_dict[id])
        return list_assigned_cli

    def get_open_facilities(self) -> list:
        """
        get assigned facilites from connection matrix
        """
        list_assigned_fac = []
        bool_mask = (self.connection_matrix != 0).any(axis=0)
        # list_assigned_fac_id = self.connection_matrix.index[(self.connection_matrix != 0).any(axis=0)].tolist()
        list_assigned_fac_id = bool_mask.index[bool_mask].tolist()
        for id in list_assigned_fac_id:
            list_assigned_fac.append(self.data.fac_dict[id])
        return list_assigned_fac

    def get_assigned_cli_to_fac(self, facility) -> list:
        """
        get assigned clients to a given facility from connection matrix
        """
        list_assigned_cli = []
        list_assigned_cli_id = self.connection_matrix.index[self.connection_matrix[facility.id] == 1].tolist()
        for id in list_assigned_cli_id:
            list_assigned_cli.append(self.data.cli_dict[id])
        return list_assigned_cli

    def get_fac_from_cli(self, client):
        """
        TODO: get corresponding facility from client
        """
        return

    def calc_agg_demand_facility(self, facility) -> float:
        """
        calculate the aggregated demand of all clients assigned to a given facility
        """
        # find assigned clients to facility
        assigned_cli = self.connection_matrix[self.connection_matrix[facility.id] == 1].index.tolist()
        # calculate agregated demand
        agg_demand:float = 0.0
        for cli_id in assigned_cli:
            agg_demand += self.data.cli_dict[cli_id].demand
        
        return agg_demand

    def find_fac_greedy_on_cost(self,client,facility_list=[]):
        """
        find a facility for a given client based on minimum cost
        only facilities in facility_list can be used
        """
        # filter cost_matrix
        if facility_list:
            fac_list_ids = [facility.id for facility in facility_list]
            filtered_cost_matrix = self.data.cost_matrix[fac_list_ids]
        else:
            filtered_cost_matrix = self.data.cost_matrix
        fac_namex = filtered_cost_matrix.loc[client.id].idxmin()
        facility = self.data.fac_dict[fac_namex]
        return facility

    def find_fac_greedy_on_marginal_cost(self,client,facility_list=[]):
        """
        find a facility for a given client based on minimum marginal cost
        only facilities in facility_list can be used
        marginal cost: difference between assignment cost of a client to 2 facilities
        """
        # if facility list is empty use all facilities
        if not facility_list:
            facility_list = self.data.facilities
        prefs = self.get_fac_prefs()
        client_position_dict = {}
        for facility in facility_list:
            # create a dictionary with the preference position by facility
            client_position_dict[facility.id] = prefs[facility.id].index(client.id)
        fac_idx = min(client_position_dict, key=client_position_dict.get)
        facility = self.data.fac_dict[fac_idx]
        return facility
    
    def get_fac_prefs(self) -> dict:
        """
        get facility preferences from marginal cost matrix
        """
        prefs_dict = {}
        for facility in self.data.facilities:
            marg_prefs = self.data.marginal_cost_matrix[facility.id]
            marg_prefs_sorted = marg_prefs.sort_values(ascending=False)
            prefs_dict[facility.id] = marg_prefs_sorted.index.to_list()
        return prefs_dict

    def draw_net(self):
        """
        Create graph of net
        """
        net_graph = Network()
        net_melt = self.data.cost_matrix.melt(ignore_index=False).reset_index()
        net_melt["variable"] = "f"+ net_melt["variable"].astype(str)
        net_melt["index"] = "c"+ net_melt["index"].astype(str)
        for facility in self.data.facilities:
            net_graph.add_node("f"+str(facility.id), title=str(facility.id), color="red")
        for client in self.data.clients:
            net_graph.add_node("c"+str(client.id), title=str(client.id), color="blue")
        for _, row in net_melt.iterrows():
            fac_name = row["variable"]
            cli_name = row["index"]
            fac_id = int(fac_name.replace("f",""))
            cli_id = int(cli_name.replace("c",""))
            cost = row["value"]
            if self.connection_matrix.loc[cli_id, fac_id] == 1:
                net_graph.add_edge(
                    fac_name,
                    cli_name,
                    lenght = cost,
                    color = "black",
                    label = str(cost))
        net_graph.show_buttons(filter_=['physics'])
        net_graph.toggle_physics(True)
        net_graph.show(f"out/net_{self.id}.html")


class Action:
    """
    Class for handling actions on nets
    TODO: deepcopy net and assing new id?
    """
    def __init__(self, net):
        self.net = net
        self.old_net = copy.deepcopy(net)
        self.new_net = copy.deepcopy(net)
        # if not provided, assign action id based on timestamp

        self.done = False
        self.feasible:bool = True
        self.balance:float = 0.0

    def __str__(self) -> str:
        action_summary = f"""
        action INFO:
        - feasible: {self.feasible}
        - balance: {self.balance:+}
        """
        return textwrap.dedent(action_summary)

    def calculate_balance(self):
        """
        TODO: Calculate action balance
        """
        cost_ini = self.old_net.total_cost
        cost_end = self.new_net.calc_cost(verbose=False)
        balance = cost_end - cost_ini
        return balance

    @action_decorator
    def assign_cli_to_fac(self,client,facility,verbose=True):
        """
        assign client to facility
        """
        self.new_net.updated = False
        # check if already assigned
        if self.old_net.connection_matrix.loc[client.id, facility.id] == 1:
            print(f"{client} already assigned to {facility}")
            self.feasible = False
            return self
        # assign client to facility
        self.new_net.connection_matrix.loc[client.id, facility.id] = 1
        # update net
        # self.new_net.update_net(verbose=False)
        # check feasibility
        if not self.new_net.is_valid() or not self.new_net.is_capacity_ok():
            print(f"Unfeasible action: {client} cannot be assigned to {facility}")
            self.feasible = False
            self.new_net = self.net
            return self
        # calculate balance
        self.balance = self.calculate_balance()
        if verbose:
            print(f"{client} assigned to {facility}")
            print(f"balance: {self.balance:+}")
        return self

    @action_decorator
    def unassign_cli_to_fac(self,client,facility,verbose=True):
        """
        unassign client to facility
        """
        self.new_net.updated = False
        # check if already unassigned
        if self.old_net.connection_matrix.loc[client.id, facility.id] == 0:
            print(f"{client} is not assigned to {facility}")
            self.feasible = False
            return self
        # unassign client to facility
        self.new_net.connection_matrix.loc[client.id, facility.id] = 0
        # update net
        # self.new_net.update_net(verbose=False)
        # calculate balance
        self.balance = self.calculate_balance()
        if verbose:
            print(f"{client} unassigned to {facility}")
            print(f"balance: {self.balance:+}")
        return self


    @action_decorator
    def close_facility(self,facility,how="greedy_cost",verbose=True):
        """
        Composed action
        Close given facility and relocates clients using:
            - "greedy_cost": cost matrix in a greedy fashion
            - "greedy_marginal": marginal cost matrix in a greedy fashion
        """
        self.new_net.updated = False
        open_facilities = self.net.get_open_facilities()
        clients = self.net.get_assigned_cli_to_fac(facility)
        # check if already unassigned
        if facility not in open_facilities:
            print(f"{facility} is already closed")
            self.feasible = False
            return self
        open_fac_without_current = list(open_facilities)
        open_fac_without_current.remove(facility)
        for client in clients:
            # unassign client
            act_unassign= Action(self.new_net).unassign_cli_to_fac(client,facility,verbose=False)
            self.new_net = act_unassign.new_net
            # find the most convenient facility that is not closed and assign client
            best_fac = None
            while not best_fac:
                if how == "greedy_cost":
                    candidate_fac = self.net.find_fac_greedy_on_cost(client,open_fac_without_current)
                elif how == "greedy_marginal":
                    candidate_fac = self.net.find_fac_greedy_on_marginal_cost(client,open_fac_without_current)
                act_assign= Action(self.new_net).assign_cli_to_fac(client,candidate_fac,verbose=True)
                if act_assign.feasible:
                    self.new_net = act_assign.new_net
                    best_fac = candidate_fac
                else:
                    open_fac_without_current.remove(candidate_fac)
        # calculate balance
        self.balance = self.calculate_balance()
        if verbose:
            print(f"{facility} closed:")
            print(f" - greedy client reassignation: {clients}")
            print(f" - balance: {self.balance:+}")
        return self

if __name__ == "__main__":
    file_path = "inputs/Holmberg_Instances/p2"
    data = Importer(file_path)
    net = Net(1, data)

    net = Action(net).assign_cli_to_fac(data.cli_dict[3],data.fac_dict[4]).new_net
    net = Action(net).assign_cli_to_fac(data.cli_dict[15],data.fac_dict[9]).new_net
    net = Action(net).unassign_cli_to_fac(data.cli_dict[3],data.fac_dict[4]).new_net

    print(net.connection_matrix)
    print(net)
    net.draw_net()
