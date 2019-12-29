import pulp

class prim:
    def __init__(self, X_, N, S_s, primal_):
        self.X_ = X_
        self.N = N
        self.S_s = S_s
        self.primal_ = primal_


    def create_X(self, count):
        self.X_.append({})
        for i in range(self.N):
            for j in range(i + 1, self.N):
                self.X_[count][str(i) + "_" + str(j)] = pulp.LpVariable(str(i) + "_" + str(j), lowBound=0, cat='Binary')
        return self.X_

    ################################################################################
    #         DFS to find subtours S(i...N-1)                                      #
    ################################################################################

    def create_S_x(self, count):
        graph = {}
        S_x = []
        for edge in self.X_[count]:
            if self.X_[count][edge]:
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
        self.S_s.append(S_x)
        return self.S_s

    ################################################################################
    #         for S_i in S_x                                                       #
    #           add constraint: Σ (x_ij) >= 2                                      #
    #                              i ∈ S_i                                         #
    #                              j ∉ S_i                                         #
    ################################################################################

    def add_constraints(self, count, S_s):
        for i in range(self.N):
            temp = pulp.LpAffineExpression()
            for j in range(self.N):
                if i != j:
                    if i < j:
                        temp += pulp.lpSum(self.X_[count][str(i) + "_" + str(j)])
                    else:
                        temp += pulp.lpSum(self.X_[count][str(j) + "_" + str(i)])
            self.primal_[count] += temp == 2

        for S_x in self.S_s:
            for idx, S_i in enumerate(S_x):
                temp = pulp.LpAffineExpression()
                for i in S_i:
                    for S_not_including_i in S_x:
                        if S_x[idx] != S_not_including_i:
                            for j in S_not_including_i:
                                if i != j:
                                    if i < j:
                                        temp += pulp.lpSum(self.X_[count][str(i) + "_" + str(j)])
                                    else:
                                        temp += pulp.lpSum(self.X_[count][str(j) + "_" + str(i)])
                # print("lol, ", temp)
                self.primal_[count] += temp >= 2