"""

"""

from importer import Importer
from pyvis.network import Network
import copy
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

        self.initilize()
      
    def initilize(self):
        """
        All facilities are opened
        No customer is assigned to facilities
        """
        self.connection_matrix[:] = 0
        self.opened_facilities = data.facilities
        self.assigned_clients = []

    def dummy_greedy_net(self):
        """
        create dummy greedy net that:
        1. is single-source - one client per facility
        2. is valid - demand restrictions are not violated
        3. greedy: the client minimum cost is used for assigning facilities
        """
        self.check_complete()
        for client in self.data.clients:
            fac_namex = data.cost_matrix.loc[client.id].idxmin()
            [ok,new_net,balance] = Action(self).assign_cli_to_fac(client, self.data.fac_dict[fac_namex])
            if ok:
                self = new_net
        self.check_complete()
        return self

    def calc_cost(self, verbose=True) -> float:
        """
        Evaluate the total cost of the net
        total_cost = fixed_cost + variable_cost
            fixed_cost = Sum(opened_facilities)
            variable_cost = Sum(assigned_clients)
        """
        # check net first
        # if not self.check_valid():
        #     self.total_cost = 0.0
        #     print("invalid net -> cost initialized to 0.0")
        #     return
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


    def check_valid(self):
        """
        Check if the net is valid
        1. each client is assigned to only one facility
        2. capacity from facilities is not exceded
        """
        # each client is assigned to only one facility
        if self.connection_matrix.values.sum() != len(self.data.clients):
            print("Invalid net: more than one client assigned to a facility")
            # TODO: find multi-assigned facilities
            return False
        # capacity is not exceded
        for facility in self.opened_facilities:
            # calculate aggregated demand
            agg_demand = self.calc_agg_demand_facility(facility)
            # compare with facility capacity
            if facility.capacity < agg_demand:
                print(f"Invalid net: Facility {facility.id} capacity is exceded")
                return False
        
        print("Valid net")
        return True

    def check_complete(self):
        """
        check if net is complete:
        1. connection matrix matches net attributes
        2. there are not unassigned clients
        3. TODO: each open facility need to have at least one customer assigned ??
        """
        # connection matrix missmatch with net attributes (connection matrix is the reference)
        list_clients = self.get_assigned_clients()
        if set(self.assigned_clients) != set(list_clients):
            print("Incomplete net: connection matrix missmatched")
            self.assigned_clients = list_clients
            print("fixed")
        # TODO: facilities missmatch?
        # no unassigned clients
        if set(self.assigned_clients) != set(self.data.clients):
            print("Incomplete net: there are unassigned clients")
            # TODO: find unassigned clients
            return False

        print("Complete net")
        return True

    def get_assigned_clients(self) -> list:
        """
        get assigned clients from connection matrix
        """
        list_assigned_cli = []
        list_assigned_cli_id = self.connection_matrix[self.connection_matrix.eq(1).any(axis=1)].index.tolist()
        for id in list_assigned_cli_id:
            list_assigned_cli.append(self.data.cli_dict[id])
        return list_assigned_cli

    def get_assigned_cli_to_fac(self, facility) -> list:
        """
        get assigned clients to a given facility from connection matrix
        """
        list_assigned_cli = []
        list_assigned_cli_id = self.connection_matrix.index[self.connection_matrix[facility.id] == 1].tolist()
        for id in list_assigned_cli_id:
            list_assigned_cli.append(self.data.cli_dict[id])
        return list_assigned_cli

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
        net_graph.show(f"net_graph_{self.id}.html")


class Action:
    """
    Class for handling actions on nets
    TODO: deepcopy net and assing new id?
    """
    def __init__(self, net):
        self.old_net = copy.copy(net)
        self.new_net = copy.copy(net)
        # if not provided, assign action id based on timestamp

        self.feasible:bool = True
        self.balance:float = 0.0

    def __str__(self) -> str:
        action_summary = f"""
        feasible: {self.feasible}
        balance: {self.balance}
        """
        return action_summary


    @action_decorator
    def open_fac(self, facility):
        """
        open a given facility
        """
        # check if already open
        if facility in self.old_net.opened_facilities:
            print(f"Facility {facility.id} already opened")
            self.feasible = False
            return self.feasible, self.old_net, self.balance
        # add to net opened facilities
        self.new_net.opened_facilities.append(facility)
        # check net
        if not self.new_net.check_valid():
            self.feasible = False
            return self.feasible, self.old_net, self.balance
        # calculate balance
        cost_ini = self.old_net.total_cost
        cost_end = self.new_net.calc_cost(verbose=False)
        self.balance = cost_ini - cost_end

        return self

    @action_decorator
    def close_fac(self, facility, verbose=False):
        """
        close a given facility
        """
        # check if already close
        if facility not in self.old_net.opened_facilities:
            print(f"Facility {facility.id} already close")
            self.feasible = False
            return self.feasible, self.old_net, self.balance
        # remove assigned clients
        list_assigned_cli = self.old_net.get_assigned_cli_to_fac(facility)
        for client in list_assigned_cli:
            self.old_net.assigned_clients.remove(client)
        # remove from connection matrix
        self.new_net.connection_matrix[facility.id] = 0
        # remove fron net opened facilities
        self.new_net.opened_facilities.remove(facility)
        # check net
        # if not self.new_net.check_valid():
        #     self.feasible = False
        #     return self.feasible, self.old_net, self.balance
        # calculate balance
        cost_ini = self.old_net.total_cost
        cost_end = self.new_net.calc_cost(verbose=False)
        self.balance = cost_ini - cost_end

        return self

    @action_decorator
    def assign_cli_to_fac(self,client,facility):
        """
        assign client to facility
        """
        # check if already assigned
        if self.old_net.connection_matrix.loc[client.id, facility.id] == 1:
            print(f"Client {client.id} already assigned to Facility {facility.id}")
            self.feasible = False
            return self.feasible, self.old_net, self.balance
        self.new_net.connection_matrix.loc[client.id, facility.id] = 1
        print(f"Client {client.id} assigned to Facility {facility.id}")
        # print(self.connection_matrix)
        self.new_net.assigned_clients.append(client)
        # TODO: calculate balance
        cost_ini = self.old_net.total_cost
        cost_end = self.new_net.calc_cost(verbose=False)
        self.balance = cost_ini - cost_end

        return self


if __name__ == "__main__":
    file_path = "inputs/Holmberg_Instances/p2"
    data = Importer(file_path)
    net = Net(1, data)
    # print(data.cost_matrix)
    # net.draw_net()
    # net.calc_cost()
    # open_fac = Action(net).open_fac(data.fac_dict[3])
    # net = net.dummy_greedy_net()
    print(net.connection_matrix)
    net.calc_cost()
    action = Action(net).close_fac(data.fac_dict[1])
    action2 = Action(net).assign_cli_to_fac(data.cli_dict[1],data.fac_dict[1])
    new = action2.new_net
    old = action2.old_net
    print(action2.balance)
    print(action2)
    print("net")
    print(net.connection_matrix)
    net.calc_cost()
    print("new")
    print(new.connection_matrix)
    new.calc_cost()
    print("old")
    print(old.connection_matrix)
    old.calc_cost()
