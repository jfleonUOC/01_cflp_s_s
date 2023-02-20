"""

"""

from importer import Importer
from network import Net, Action
import os
import copy
import datetime
import time

class Heuristic:
    """
    Class for handling heuristics
    """
    def __init__(self, net):
        self.net = net

    def execute(self):
        pass

def dummy_greedy_net(data, name="dummy_1", how="greedy_cost"):
    """
    create dummy greedy net that:
    1. is single-source - one facility per client
    2. is valid - demand restrictions are not violated
    3. greedy: the client minimum cost is used for assigning facilities
    """
    net = Net(name, data)

    for client in data.clients:
        feasible_fac = False
        facility_list = copy.copy(net.data.facilities)
        while not feasible_fac:
            if how == "greedy_cost":
                facility = net.find_fac_greedy_on_cost(client,facility_list)
            if how == "greedy_marginal":
                facility = net.find_fac_greedy_on_marginal_cost(client,facility_list)
            act = Action(net).assign_cli_to_fac(client, facility)
            feasible_fac = act.feasible
            # print(facility_list)
            # print(facility)
            facility_list.remove(facility)
        net = act.new_net
    print(20*"*")
    print("Greedy net created")
    net.check()
    print(20*"*")
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


def calculate_savings(net, how="greedy_cost", verbose=True) -> dict:
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
    if verbose:
        print(savings_sorted)

    return savings_sorted

def savings_heur(file_path="", initial="greedy_cost", save="greedy_cost", close="greedy_cost", verbose=False):
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
    # folder = "Holmberg_Instances/"
    # folder = "OR-Library_Instances/"
    # folder = "Yang_Instances/"
    # subfolder = ""
    # subfolder = "30-200/"
    # instance = "p13"
    # instance = "cap134"
    # instance = "30-200-1.dat"
    # file_path = "inputs/"+folder+subfolder+instance

    if file_path == "":
        # ask for instance input
        data = Importer()
    else:
        data = Importer(file_path)
    # create network name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = data.instance_type+"_"+data.instance+"_"+timestamp

    # 1. initial assignment
    print("""*** Initial assignment ***""")
    net = dummy_greedy_net(data, name=output_name, how=initial)

    # 2. closing facilities loop
    max_iteration = 200
    iteration = 0
    while True:
        # 2.1. calculate savings list
        if verbose:
            print("""*** Calculating savings list ***""")
        savings = calculate_savings(net, how=save)
        # 2.2. checks 
        if verbose:
            print("""*** Checking ***""")
        # 2.2.1. empty list
        if not savings:
            print("> exiting: savings list is empty")
            break
        # 2.2.2. valid solution
        if not net.check():
            print("> exiting: net did not pass checks")
            break
        # 2.2.3. positive balance of next facility
        if next(iter(savings.values())) > -0.0:
            print("> exiting: cannot save more cost")
            break
        # 2.3. execute facility closure
        if verbose:
            print("""*** Closing facility ***""")
        facility = next(iter(savings.keys()))
        act_close = Action(net).close_facility(facility,how=close)
        net = act_close.new_net
        # safety loop break
        iteration += 1
        print(f"> {iteration=} finished: {facility} was closed")
        if iteration >= max_iteration:
            print(f"> limit reached: {iteration} iterations")
            break

    # print(net.connection_matrix)
    print(net)
    # net.draw_net()
    return net


def test_2():
    # TEST 2 - close facilities from greedy
    net = dummy_greedy_heur()
    print("--sep")
    savings = calculate_savings(net)
    print("--sep")
    act = Action(net).close_facility_greedy(net.data.fac_dict[2])
    net = act.new_net
    print(net.total_cost)
    print("--sep")
    savings = calculate_savings(net)
    print("--sep")
    act = Action(net).close_facility_greedy(net.data.fac_dict[2])
    net = act.new_net
    print(net.total_cost)
    print("--sep")
    act = Action(net).close_facility_greedy(net.data.fac_dict[10])
    net = act.new_net
    print(net.total_cost)
    print("--sep")
    savings = calculate_savings(net)

def test_3():
    # TEST 3 - assign marginal with list of facilities
    file_path = "inputs/Holmberg_Instances/p2"
    data = Importer(file_path)
    net = Net("dummy_1", data)
    client = data.cli_dict[3]
    facility_list = [data.fac_dict[4],data.fac_dict[2]]
    fac_prefs = net.get_fac_prefs()
    print(fac_prefs)
    cli_pref = net.find_fac_greedy_on_marginal_cost(data.cli_dict[17])
    print(cli_pref)
    cli_pref = net.find_fac_greedy_on_marginal_cost(data.cli_dict[17],facility_list)
    print(cli_pref)

def loop_all():
    output = {}
    folder = "inputs/Holmberg_Instances/"
    # root = "inputs/OR-Library_Instances/"
    # root = "inputs/Yang_Instances/"
    instances = [item for item in os.listdir(folder) if os.path.isfile(os.path.join(folder,item))]
    instances = ["p25"]
    # for instance in instances[:2]: # first N
    # for instance in instances[18:]: # from N to end
    for instance in instances:
        path = folder+instance
        start_time = time.time()
        out_net = savings_heur(path, initial="greedy_marginal", save="greedy_marginal", close="greedy_marginal", verbose=True)
        end_time = time.time()
        elapsed_time = end_time - start_time
        output[instance] = [out_net.total_cost, elapsed_time]
        print("RESULTS")
        for key, value in output.items():
            print(f"{key},{value}")


if __name__ == "__main__":
    # dummy_greedy_heur(how="greedy_marginal")
    # savings_heur(initial="greedy_cost", save="greedy_cost", close="greedy_cost")
    # savings_heur(initial="greedy_marginal", save="greedy_marginal", close="greedy_marginal")
    loop_all()
