"""This class contains the functions needed for the primal LP. It uses an open-source LP solver (Pulp) to carry out the
calculations.
"""

import pulp

class Primal:
    def __init__(self, X_, N, S_s, primal_):
        """"""
        self.X_ = X_
        self.N = N
        self.S_s = S_s
        self.primal_ = primal_

    def create_X(self, iteration):
        """This function creates a list of variables that tells you if a path from a city to another is taken."""
        self.X_.append({})
        for city_i in range(self.N):
            for city_j in range(city_i + 1, self.N):
                self.X_[iteration][str(city_i) + "_" + str(city_j)] = pulp.LpVariable(str(city_i) + "_" + str(city_j),
                                                                                      lowBound=0, cat='Binary')
        return self.X_

    def create_S_x(self, iteration):
        """In order to create S_x, we need to use a DFS to find connecting cities. This will be the relevant subtours."""
        graph = {}
        S_x = []
        for edge in self.X_[iteration]:
            if self.X_[iteration][edge]:
                xs = edge.split("_")
                start = int(xs[0])
                end = int(xs[1])
                graph[start] = graph.get(start, []) + [end]
                graph[end] = graph.get(end, []) + [start]

        visited = set()
        for node in graph:
            if node not in visited:
                stack = [node]
                res = []
                while stack:
                    vtx = stack.pop()
                    if vtx not in visited:
                        res.append(vtx)
                        visited.add(vtx)
                        if vtx in graph:
                            for next in graph[vtx]:
                                if next not in visited:
                                    stack.append(next)
                S_x.append(res)
        return S_x

    def add_to_S_s(self, S_x):
        """S_x is added to the S_s"""
        self.S_s.append(S_x)

    def add_constraints(self, iteration):
        """Adds constraints for the current iteration while keeping the constraints from old tours as well:
           First, a city's path to all other cities = 2, because we enter and exit that city once.
           For the subtours, we add the constraints:
                for S_x in S_x
                    add constraint: Σ (x_ij) >= 2
                                    i ∈ S_i
                                    j ∉ S_i
        """
        for city_i in range(self.N):
            temp = pulp.LpAffineExpression()
            for city_j in range(self.N):
                if city_i != city_j:
                    if city_i < city_j:
                        temp += pulp.lpSum(self.X_[iteration][str(city_i) + "_" + str(city_j)])
                    else:
                        temp += pulp.lpSum(self.X_[iteration][str(city_j) + "_" + str(city_i)])
            self.primal_[iteration] += temp == 2

        for S_x in self.S_s:
            for idx, S_i in enumerate(S_x):
                temp = pulp.LpAffineExpression()
                for city_i in S_i:
                    for S_not_including_i in S_x:
                        if S_x[idx] != S_not_including_i:
                            for city_j in S_not_including_i:
                                if city_i != city_j:
                                    if city_i < city_j:
                                        temp += pulp.lpSum(self.X_[iteration][str(city_i) + "_" + str(city_j)])
                                    else:
                                        temp += pulp.lpSum(self.X_[iteration][str(city_j) + "_" + str(city_i)])
                self.primal_[iteration] += temp >= 2
