import pulp
import math
class dual:

    def __init__(self, Ys_, dual_, radii_, N):
        self.Ys_ = Ys_
        self.dual_ = dual_
        self.radii_ = radii_
        self.N = N

    # Ys_Tour0_0 first tour is 0
    def create_Ys(self, S_s, count):
        self.Ys_.append({})
        for idx, S_x in enumerate(S_s):
            for i in range(len(S_x)):
                self.Ys_[count]["Ys_tour" + str(idx) + "_" + str(i)] =\
                    pulp.LpVariable("Ys_tour" + str(idx) + "_" + str(i), lowBound = 0, cat = 'Continuous')

    def dist(self, p1, p2):  # takes tuple
        # calculates distance between two cities
        distance = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))
        return distance

    def add_constraints_Y(self, S_s, count, G):
        for i in range(self.N):
            for j in range(i + 1,self.N):
                self.dual_[count] += self.radii_[count]["r_" + str(i)] + self.radii_[count]["r_" + str(j)] <= self.dist(G[i],
                                                                                                        G[j])
        for idx, S_x in enumerate(S_s):
            for idx_start, subgroup in enumerate(S_x):
                for idx_i, i in enumerate(subgroup):
                    for idx_end in range(idx_start + 1, len(S_x)):
                        for j in S_x[idx_end]:
                            temp = 0
                            for idx1, S_x_ in enumerate(S_s):
                                for idx2, S_i in enumerate(S_x_):
                                    if i in S_i and j in S_i:
                                        break
                                    elif i in S_i or j in S_i:
                                        temp += self.Ys_[count]["Ys_tour" + str(idx1) + "_" + str(idx2)]

                            if (i,j) == (9, 10):
                                print("start: ", idx_start, idx_i, idx_end, (i, j))
                                print("end: ", temp)
                                print("rest: ", (self.radii_[count]["r_" + str(i)] + self.radii_[count]["r_" + str(j)] + temp <= self.dist(G[i], G[j])))

                            self.dual_[count] += (self.radii_[count]["r_" + str(i)] + self.radii_[count]["r_" + str(j)]
                                                 + temp <= self.dist(G[i], G[j]))