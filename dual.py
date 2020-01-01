import pulp
import math

class dual:
    def __init__(self, Ys_, dual_, radii_, N):
        self.Ys_ = Ys_
        self.dual_ = dual_
        self.radii_ = radii_
        self.N = N

    # Ex: Ys_Tour0_0: at iteration 0, Ys for subtour 0
    def create_Ys(self, S_s, count):
        self.Ys_.append({})
        for idx, S_x in enumerate(S_s):
            for i in range(len(S_x)):
                self.Ys_[count]["Ys_tour" + str(idx) + "_" + str(i)] =\
                    pulp.LpVariable("Ys_tour" + str(idx) + "_" + str(i), lowBound=0, cat='Continuous')

    def dist(self, p1, p2):  # Takes tuple
        # Calculates distance between two cities
        distance = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))
        return distance

    def add_constraints_Y(self, S_s, count, G):
        for i in range(self.N):
            for j in range(i + 1,self.N):
                self.dual_[count] += self.radii_[count]["r_" + str(i)] + self.radii_[count]["r_" + str(j)] \
                                     <= self.dist(G[i], G[j])
        for idx, S_x in enumerate(S_s):
            for idx_start, subgroup in enumerate(S_x):
                for idx_i, city_start in enumerate(subgroup):
                    for idx_end in range(idx_start + 1, len(S_x)):
                        for city_end in S_x[idx_end]:
                            temp = 0
                            for idx1, S_x_ in enumerate(S_s):
                                for idx2, S_i in enumerate(S_x_):
                                    if city_start in S_i and city_end in S_i:
                                        break
                                    elif city_start in S_i or city_end in S_i:
                                        temp += self.Ys_[count]["Ys_tour" + str(idx1) + "_" + str(idx2)]
                            self.dual_[count] += (self.radii_[count]["r_" + str(city_start)]
                                                  + self.radii_[count]["r_" + str(city_end)]
                                                  + temp <= self.dist(G[city_start], G[city_end]))
