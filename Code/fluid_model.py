"""
 First stage of embedding -- capacity planning using an LP model
"""

from gurobipy.gurobipy import quicksum, Model, GRB
from distance import GraphUtilities
import vEntities
from layout import Style as style


class LinearProgramSolver:
    def __init__(self, applications, grouped_users, graph):
        self.applications = applications
        self.grouped_users = grouped_users
        self.graph = graph
        self.model = Model("placement")
        self.utils = GraphUtilities(graph)
        self.direct = {}  # Initialize the variable
        self.transient = {}  # Initialize the variable

    def define_variables(self):
        """
        Defining variables for the LP model, which are two continuous variables, namely 'direct' and 'transient' variables
        """
        for a in self.applications:
            for i, j in a.edges():  # Ensure edges() is callable
                for s in self.graph.nodes():
                    for m, n in self.graph.edges():
                        self.direct[a, s, i, j, m, n] = self.model.addVar(vtype=GRB.CONTINUOUS, lb=0,
                                                                          name=f'Direct [{a.name}, {s}, {i}, {j}, {m}, {n}]')
                        self.transient[a, s, i, j, m, n] = self.model.addVar(vtype=GRB.CONTINUOUS, lb=0,
                                                                             name=f'Transient [{a.name}, {s}, {i}, {j}, {m}, {n}]')

        # Update the model to integrate the new variables
        self.model.update()

    def setup_objective_function(self):
        """
        Set up the objective function for the linear programming model.

        The objective function aims to minimize the cost associated with the 'direct' and 'transient' variables.
        Costs are calculated based on the 'shareCost' of edges and nodes in the graph and the 'shareMultiplier'
        of the edges and nodes in each application.
        """
        # Objective function components are generated using a list comprehension
        objective_components = (
            # Calculate cost for transient variables
            (self.transient[a, s, i, j, m, n] * self.graph.edges[(m, n)]['shareCost'] * a.edges[(i, j)][
                'shareMultiplier'])
            # Calculate cost for direct variables
            + self.direct[a, s, i, j, m, n] * (
                    self.graph.edges[(m, n)]['shareCost'] * a.edges[(i, j)]['shareMultiplier']
                    + self.graph.nodes[n]['shareCost'] * a.nodes[j]['shareMultiplier'])
            # Iterate over all combinations of applications, edges, and graph nodes
            for a in self.applications for i, j in a.edges() for s in self.graph.nodes()
            for m in self.graph.nodes() for n in self.graph.nodes() if (m, n) in self.graph.edges()
        )

        # Setting up the objective function in the model to minimize the total cost
        self.model.setObjectiveN(quicksum(objective_components), GRB.MINIMIZE)
        # Update the model after setting the objective function
        self.model.update()

    def setup_constraints(self):
        self.no_flow_loops_no_local_transient_constraints()
        self.local_terminator_constraint_constraint()
        self.direct_flow_preservation_constraint()
        self.transient_flow_preservation_constraint()
        self.demand_satisfaction_constraints_constraint()
        self.datacenter_capacity_constraints_constraint()
        self.link_capacity_constraints()
        self.single_hop_latency_constraints()
        self.monotonic_allocation_and_latency_bounds()

    def no_flow_loops_no_local_transient_constraints(self):
        """
        Add constraints to the model to prevent flow loops and local transient flows.
        - 'NO FLOW LOOPS' ensures no direct or transient flows between a node and itself.
        - 'NO LOCAL TRANSIENT' ensures no transient flows within the same node.
        """

        def no_flow_loops_constraint(s, m):
            """
            Add 'NO FLOW LOOPS' constraints for nodes s and m.
            """
            self.model.addConstr(quicksum(self.direct[a, s, i, j, m, s] for a in self.applications
                                          for i, j in a.edges()) == 0, name="NO FLOW LOOPS")
            self.model.addConstr(quicksum(self.transient[a, s, i, j, m, s] for a in self.applications
                                          for i, j in a.edges()) == 0, name="NO FLOW LOOPS")

        def no_local_transient_constraint(s, m):
            """
            Add 'NO LOCAL TRANSIENT' constraints for nodes s and m.
            """
            self.model.addConstr(quicksum(self.direct[a, s, i, j, m, m] for a in self.applications
                                          for i, j in a.edges()) == 0, name="NO LOCAL TRANSIENT")
            self.model.addConstr(quicksum(self.transient[a, s, i, j, m, m] for a in self.applications
                                          for i, j in a.edges()) == 0, name="NO LOCAL TRANSIENT")
            self.model.addConstr(quicksum(self.transient[a, s, i, j, s, s] for a in self.applications
                                          for i, j in a.edges()) == 0, name="NO LOCAL TRANSIENT")

        for s in self.graph.nodes:
            for m in self.graph.nodes:
                if m != s:
                    # Add constraints to prevent flow loops for edges that exist in the graph
                    if (m, s) in self.graph.edges:
                        no_flow_loops_constraint(s, m)

                    # Add constraints to prevent local transient flows
                    no_local_transient_constraint(s, m)

    def local_terminator_constraint_constraint(self):
        """
        Add local terminator constraints to the model.
        This constraint ensure that there is no direct flows into the 'terminator' func -T- between two physical nodes.
        """
        for m, n in self.graph.edges:
            if m != n:
                for s in self.graph.nodes:
                    for a in self.applications:
                        for i, j in a.edges():
                            if j == 'T':
                                self.model.addConstr(self.direct[a, s, i, j, m, n] == 0, name="LOCAL TERMINATOR")

    def direct_flow_preservation_constraint(self):
        """
        Add direct flow preservation constraints to the model.
        These constraints ensure that for each application and node, the sum of incoming direct flows
        is equal to the sum of outgoing direct and transient flows.
        """
        # Iterate over each node, application, and their edges
        for d in self.graph.nodes:
            for a in self.applications:
                for i, j in a.edges():
                    for j_, k in a.edges():
                        # Check if the outgoing node j is the same in both edges (i, j) and (j_, k)
                        if j == j_:
                            # Sum of incoming direct flows
                            incoming_direct_flows = quicksum(self.direct[a, s, i, j, m, d]
                                                             for s in self.graph.nodes
                                                             for m in self.graph.nodes
                                                             if (m, d) in self.graph.edges())
                            # Sum of outgoing direct and transient flows
                            outgoing_flows = quicksum(self.direct[a, d, j, k, d, n] + self.transient[a, d, j, k, d, n]
                                                      for n in self.graph.nodes
                                                      if (d, n) in self.graph.edges())

                            # Add the flow preservation constraint
                            self.model.addConstr(incoming_direct_flows - outgoing_flows == 0,
                                                 name="DIRECT FLOW PRESERVATION")

    def transient_flow_preservation_constraint(self):
        """
        Add transient flow preservation constraints to the model.
        These constraints ensure that for each pair of different nodes (s, d), each application,
        and each edge in the application, the sum of incoming transient flows to node d equals
        the sum of outgoing direct and transient flows from node d.
        """
        # Iterate over each pair of distinct nodes, each application, and each edge in the application
        for s in self.graph.nodes:
            for d in self.graph.nodes:
                if s != d:  # Ensure s and d are different nodes
                    for a in self.applications:
                        for i, j in a.edges():
                            # Sum of incoming transient flows to node d
                            incoming_transient_flows = quicksum(self.transient[a, s, i, j, m, d]
                                                                for m in self.graph.nodes
                                                                if m != d and (m, d) in self.graph.edges())

                            # Sum of outgoing direct and transient flows from node d
                            outgoing_flows = quicksum(self.direct[a, s, i, j, d, n] + self.transient[a, s, i, j, d, n]
                                                      for n in self.graph.nodes
                                                      if n != s and n != d and (d, n) in self.graph.edges())

                            # Add the transient flow preservation constraint
                            self.model.addConstr(incoming_transient_flows - outgoing_flows == 0,
                                                 name="TRANSIENT FLOW PRESERVATION")

    def demand_satisfaction_constraints_constraint(self):
        """
        Add demand satisfaction constraints to the model.
        These constraints ensure that for each application and each data center node,
        the aggregate demand is balanced by the sum of direct and transient flows.
        """
        # Iterate over each node and application
        for d in self.graph.nodes:
            for a in self.applications:
                # Iterate over each edge in the application
                for u, k in a.edges():
                    # Apply constraint only if the source node is 'U' (user node)
                    if u == 'U':
                        # Calculate the aggregate demand at data center 'd' for application 'a'
                        aggregate_demand = vEntities.get_aggregate_dc_demand(a, self.grouped_users, d)

                        # Calculate the sum of direct and transient flows at data center 'd'
                        total_flows = quicksum(self.direct[a, d, u, k, d, n] + self.transient[a, d, u, k, d, n]
                                               for n in self.graph.nodes
                                               if (d, n) in self.graph.edges())

                        # Add the demand satisfaction constraint
                        self.model.addConstr(aggregate_demand - total_flows == 0,
                                             name="DEMAND SATISFACTION")

    def datacenter_capacity_constraints_constraint(self):
        """
        Add data center capacity constraints to the model.
        These constraints ensure that for each data center node, the total weighted flows do not exceed the data center's capacity.
        The flow weights are determined by the 'shareMultiplier' of each node in each application.
        """
        # Iterate over each data center node
        for d in self.graph.nodes:
            # Calculate the total weighted flows to the data center
            total_flows = quicksum(a.nodes[j]['shareMultiplier'] *
                                   quicksum(self.direct[a, s, i, j, m, d]
                                            for m in self.graph.nodes if (m, d) in self.graph.edges())
                                   for s in self.graph.nodes for a in self.applications for i, j in a.edges())

            # Add a constraint that the total flows must not exceed the data center's capacity
            self.model.addConstr(total_flows <= self.graph.nodes[d]['shareCap'],
                                 name="DATACENTER CAPACITY")

    def link_capacity_constraints(self):
        """
        Add link capacity constraints to the model.
        These constraints ensure that for each link in the network, the total weighted flows do not exceed the link's capacity.
        The flow weights are determined by the 'shareMultiplier' of each edge in each application.
        """
        # Iterate over each pair of nodes (potential link)
        for m in self.graph.nodes:
            for n in self.graph.nodes:
                # Apply the constraint only if there is an edge (link) between nodes m and n
                if (m, n) in self.graph.edges:
                    # Calculate the total weighted flows through the link
                    total_flows = quicksum(a.edges[(i, j)]['shareMultiplier'] *
                                           quicksum(self.direct[a, s, i, j, m, n] + self.transient[a, s, i, j, m, n]
                                                    for s in self.graph.nodes) for a in self.applications for i, j in
                                           a.edges())

                    # Add a constraint that the total flows must not exceed the link's capacity
                    self.model.addConstr(total_flows <= self.graph.edges[(m, n)]['shareCap'],
                                         name="LINK CAPACITY")

    def single_hop_latency_constraints(self):
        """
        Add single hop latency constraints to the model.
        These constraints ensure that for each application, edge, and network link,
        the latency demands are met by the direct and transient flows.
        """
        # Iterate over each application, its edges, and pairs of nodes
        for a in self.applications:
            for i, j in a.edges():
                for s in self.graph.nodes():
                    for n in self.graph.nodes:
                        # Apply the constraint only if there is an edge between nodes s and n
                        if (s, n) in self.graph.edges():
                            # Latency requirement for the application edge
                            latency_req = a.edges[(i, j)]['latencyDemand'] - self.graph.edges[(s, n)]['distance']

                            # Add latency constraints for direct and transient flows
                            self.model.addConstr(self.direct[a, s, i, j, s, n] * latency_req >= 0,
                                                 name="SINGLE HOP LATENCY")
                            self.model.addConstr(self.transient[a, s, i, j, s, n] * latency_req >= 0,
                                                 name="SINGLE HOP LATENCY")

    def monotonic_allocation_and_latency_bounds(self):
        """
        Add monotonic allocation and latency bound constraints to the model.
        - Monotonic allocation ensures that flows are directed progressively away from the source.
        - Latency bounds ensure that the latency requirements for each edge in the applications are not exceeded.
        """
        # Iterate over each application, its edges, and each pair of nodes in the graph
        for a in self.applications:
            for i, j in a.edges():
                for s in self.graph.nodes():
                    for m, n in self.graph.edges():
                        # Apply constraints only if nodes m and n are different from the source s
                        if m != s and n != s:
                            # Check for monotonic allocation
                            monotonicity = self.utils.is_monotonic(s, m, n)
                            self.model.addConstr(self.direct[a, s, i, j, m, n] * monotonicity >= 0,
                                                 name="MONOTONIC ALLOCATION")
                            self.model.addConstr(self.transient[a, s, i, j, m, n] * monotonicity >= 0,
                                                 name="MONOTONIC ALLOCATION")

                            # Enforce latency bounds for direct flows
                            latency_bound = a.edges[(i, j)]['latencyDemand'] - self.utils.distance(s, n)
                            self.model.addConstr(self.direct[a, s, i, j, m, n] * latency_bound >= 0,
                                                 name='LATENCY BOUND')


    def execute_model(self):
        self.model.Params.IntFeasTol = 1e-1
        self.model.optimize()

    def handle_results(self):
        if self.model.Status in (GRB.INF_OR_UNBD, GRB.INFEASIBLE, GRB.UNBOUNDED):
            print(f'{style.RED}Model cannot be solved because it is infeasible or unbounded {style.END}')
            return [self.model, {('_', '_', '_', '_', '_', '_'): '_'}, {('_', '_', '_', '_', '_', '_'): '_'}]

        if self.model.Status != GRB.OPTIMAL:
            print(f'{style.RED}Optimization was stopped with status {style.END}' + str(self.model.Status))
            return [self.model, {('_', '_', '_', '_', '_', '_'): '_'}, {('_', '_', '_', '_', '_', '_'): '_'}]

        return self.model.getVars()

    def solve(self):
        self.model.reset()
        self.define_variables()
        self.setup_objective_function()
        self.setup_constraints()
        self.execute_model()
        self.handle_results()

    def print_results(self):
        """
        Print the results of the fluid model and return the model along with total costs.
        """
        # Print header
        self.print_header("Results of the Fluid Model")
        self.print_header("******** First stage of allocations (planning) ********", False)

        # Calculate and print the total cost of direct and transient allocations
        total_cost_direct = self.calculate_and_print_costs('Direct', self.direct)
        total_cost_trans = self.calculate_and_print_costs('Transient', self.transient)

        self.print_output('Transient', self.direct)
        self.print_output('Direct', self.transient)

        # Return model and total costs
        return [self.model, self.direct, self.transient, total_cost_direct + total_cost_trans]

    @staticmethod
    def print_header(title, with_line=True):
        """
        Print a header for the results section.
        """
        if with_line:
            print(f"{style.YELLOW}{'=' * 70}{style.END}")
            print(f"{style.BOLD}{style.DARKCYAN}{title}{style.END}")
            print(f"{style.YELLOW}{'=' * 70}{style.END}")
        else:
            print(f"{style.YELLOW}{style.BOLD} {title}{style.END}")

    def calculate_and_print_costs(self, allocation_type, allocation_variable):
        """
        Calculate and print the total costs for a given allocation type (Direct/Transient).
        """
        import network_config as nc
        fictitious = 'dc_edge' + str(nc.number_of_dc_edge + 1)
        total_cost, total_shares_alloc = 0, 0

        for a in self.applications:
            for i, j in a.edges():
                for s, m, n in self.get_valid_flows(allocation_variable, a, fictitious):
                    cost, shares = self.calculate_cost_and_shares(allocation_variable, a, s, i, j, m, n, self.graph,
                                                                  allocation_type)
                    total_cost += cost
                    total_shares_alloc += shares
                    self.print_allocation_details(allocation_type, a, s, i, j, m, n, shares)

        print(
            f'{style.PURPLE}{style.UNDERLINE}Total allocated (consumed capacity) shares to the {allocation_type} links is: '
            f'{total_shares_alloc}{style.END}')
        return total_cost

    def get_valid_flows(self, variable, application, fictitious):
        """
        Generator function to yield valid flows from the variable, excluding flows involving the fictitious node.
        """
        for i, j in application.edges():
            for s in self.graph.nodes:
                for m, n in self.graph.edges():
                    if variable[application, s, i, j, m, n].X and s != fictitious and m != fictitious and n != fictitious:
                        yield s, m, n

    @staticmethod
    def calculate_cost_and_shares(variable, application, s, i, j, m, n, graph, variable_name):
        """
        Calculate the cost and shares allocated for a given flow.
        """
        value = application.edges[(i, j)]['shareMultiplier'] * variable[application, s, i, j, m, n].X
        cost = 0
        if variable_name == 'Direct':
            cost = value * (graph.edges[(m, n)]['shareCost'] + graph.nodes[n]['shareCost'])
        elif variable_name == "Transient":
            cost = value * graph.edges[(m, n)]['shareCost']
        return cost, value

    @staticmethod
    def print_allocation_details(variable_name, application, s, i, j, m, n, shares):
        """
        Print the details of each allocation.
        """
        if not shares:
            print(
                f"{variable_name}: {application.name} {s} {i} {j} {m} {n} ----> 0 {style.BOLD}{style.GREEN}"
                f"(No effect on the actual consumed capacity){style.END}")
        else:
            print(f"{variable_name}: {application.name} {s} {i} {j} {m} {n} ----> {shares}")
