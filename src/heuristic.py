"""

"""

from importer import Importer
from network import Net, Action
import copy
import datetime

class Heuristic:
    """
    Class for handling heuristics
    """
    def __init__(self, net):
        self.net = net

    def execute(self):
        pass

# TODO: duplicated - delete
def find_fac_greedy_on_cost_old(net,client,facility_list=[]):
    """
    OLD - DELTE IF NOT USED
    find a facility for a given client based on minimum cost
    only facilities in facility_list can be used
    """
    # filter cost_matrix
    if facility_list:
        fac_list_ids = [facility.id for facility in facility_list]
        filtered_cost_matrix = net.data.cost_matrix[fac_list_ids]
    else:
        filtered_cost_matrix = net.data.cost_matrix
    fac_namex = filtered_cost_matrix.loc[client.id].idxmin()
    facility = net.data.fac_dict[fac_namex]
    return facility

def dummy_greedy_net(data, name="dummy_1", how="greedy_cost"):
    """
    create dummy greedy net that:
    1. is single-source - one facility per client
    2. is valid - demand restrictions are not violated
    3. greedy: the client minimum cost is used for assigning facilities
    """
    net = Net(name, data)

    for client in data.clients:
        if how == "greedy_cost":
            facility = net.find_fac_greedy_on_cost(client)
        if how == "greedy_marginal":
            facility = net.find_fac_greedy_on_marginal_cost(client)
        act = Action(net).assign_cli_to_fac(client, facility)
        if act.feasible:
            net = act.new_net
    net.check()
    
    return net

def dummy_greedy_heur(how="greedy_cost"):
    """
    execute a greedy net heuristic based on input file
    """
    file_path = "inputs/Holmberg_Instances/p2"
    data = Importer(file_path)
    net = dummy_greedy_net(data, how=how)

    print(net.connection_matrix)
    print(net)
    net.draw_net()

    return net

def calculate_savings_old(net) -> dict:
    """
    OLD - DELETE IF NOT USED
    calculate savings list (dictionary)
    TODO: sorted or biased randomized?
    """
    savings = {}
    # get open facilities
    open_facilities = net.get_open_facilities()
    # print(open_facilities)
    for facility in open_facilities:
        clients = net.get_assigned_cli_to_fac(facility)
        s_net = copy.deepcopy(net)
        fac_saving = 0.0
        open_fac_without_current = list(open_facilities)
        open_fac_without_current.remove(facility)
        for client in clients:
            # unassign client
            act_unassign= Action(s_net).unassign_cli_to_fac(client,facility)
            fac_saving += act_unassign.balance
            s_net = act_unassign.new_net
            # find the most convenient facility that is not closed and assign client
            best_fac = net.find_fac_greedy_on_cost(client,open_fac_without_current)
            act_assign= Action(s_net).assign_cli_to_fac(client,best_fac)
            fac_saving += act_assign.balance
            s_net = act_assign.new_net
        savings[facility] = fac_saving
    # sort list
    savings_sorted = dict(sorted(savings.items(), key=lambda item: item[1]))
    print(savings_sorted)

    return savings_sorted

def calculate_savings(net, how="greedy_cost") -> dict:
    """
    calculate savings list (dictionary)
    TODO: sorted or biased randomized?
    """
    savings = {}
    # get open facilities
    open_facilities = net.get_open_facilities()
    # print(open_facilities)
    for facility in open_facilities:
        act_close = Action(net).close_facility(facility, how=how, verbose=False)
        savings[facility] = act_close.balance
    # sort list
    savings_sorted = dict(sorted(savings.items(), key=lambda item: item[1]))
    print(savings_sorted)

    return savings_sorted

def savings_heur(initial="greedy_cost", save="greedy_cost", close="greedy_cost"):
    """
    execute the savings net heuristic based on input file
    PROCEDURE:
    1. initial assignment
    2. closing facilities loop
    2.1. calculate savings list
    2.2. checks 
    2.2.1. empty list
    2.2.2. valid solution
    2.2.3. positive balance
    2.3. execute facility closure
    """
    folder = "Holmberg_Instances"
    instance = "p2"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = folder+"_"+instance+"_"+timestamp
    file_path = "inputs/"+folder+"/"+instance
    data = Importer(file_path)

    # 1. initial assignment
    print("""*** Initial assignment ***""")
    net = dummy_greedy_net(data, name=output_name, how=initial)

    # 2. closing facilities loop
    max_iteration = 20
    iteration = 0
    while True:
        # 2.1. calculate savings list
        print("""*** Calculating savings list ***""")
        savings = calculate_savings(net, how=save)
        # 2.2. checks 
        print("""*** Checking ***""")
        # 2.2.1. empty list
        if not savings:
            break
        # 2.2.2. valid solution
        if not net.check():
            break
        # 2.2.3. positive balance of next facility
        if next(iter(savings.values())) > 0:
            break
        # 2.3. execute facility closure
        print("""*** Closing facility ***""")
        facility = next(iter(savings.keys()))
        act_close = Action(net).close_facility(facility,how=close)
        net = act_close.new_net
        # safety loop break
        iteration += 1
        if iteration >= max_iteration:
            print(f"> limit reached: {iteration} iterations")
            break

    print(net.connection_matrix)
    print(net)
    net.draw_net()
    return net


if __name__ == "__main__":
    dummy_greedy_heur(how="greedy_marginal")
    # savings_heur(initial="greedy_marginal", save="greedy_marginal", close="greedy_marginal")

    # TEST 1 - assign greedy with list of facilities
    # file_path = "inputs/Holmberg_Instances/p2"
    # data = Importer(file_path)
    # net = Net("dummy_1", data)
    # client = data.cli_dict[3]
    # facility_list = [data.fac_dict[4],data.fac_dict[2]]
    # fac = find_fac_greedy_on_cost(net,client)
    # print(fac)
    
    # TEST 2 - close facilities from greedy
    # net = dummy_greedy_heur()
    # print("--sep")
    # savings = calculate_savings(net)
    # print("--sep")
    # act = Action(net).close_facility_greedy(net.data.fac_dict[2])
    # net = act.new_net
    # print(net.total_cost)
    # print("--sep")
    # savings = calculate_savings(net)
    # print("--sep")
    # act = Action(net).close_facility_greedy(net.data.fac_dict[2])
    # net = act.new_net
    # print(net.total_cost)
    # print("--sep")
    # act = Action(net).close_facility_greedy(net.data.fac_dict[10])
    # net = act.new_net
    # print(net.total_cost)
    # print("--sep")
    # savings = calculate_savings(net)

    # TEST 3 - assign marginal with list of facilities
    # file_path = "inputs/Holmberg_Instances/p2"
    # data = Importer(file_path)
    # net = Net("dummy_1", data)
    # client = data.cli_dict[3]
    # facility_list = [data.fac_dict[4],data.fac_dict[2]]
    # fac_prefs = net.get_fac_prefs()
    # print(fac_prefs)
    # cli_pref = net.find_fac_greedy_on_marginal_cost(data.cli_dict[17])
    # print(cli_pref)
    # cli_pref = net.find_fac_greedy_on_marginal_cost(data.cli_dict[17],facility_list)
    # print(cli_pref)