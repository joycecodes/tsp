"""This class contains the functions needed for the dual LP. It creates the moats needed for the current tour
and adds the necessary constraints. The Dual uses the subtours calculated from the primal.
"""

import pulp
import math

class Dual:
    def __init__(self, Ys_, dual_, radii_, N):
        """"""
        self.Ys_ = Ys_
        self.dual_ = dual_
        self.radii_ = radii_
        self.N = N

    def create_Ys(self, S_s, count):
        """This function creates a new Ys/moat for each subtour in the current tour and carries over moats from
           previous tours. For example: Ys_tour0_0 means at iteration 0, there is a moat for subtour 0."""
        self.Ys_.append({})
        for idx_iteration, S_x in enumerate(S_s):
            for moat_i in range(len(S_x)):
                self.Ys_[count]["Ys_tour" + str(idx_iteration) + "_" + str(moat_i)] =\
                    pulp.LpVariable("Ys_tour" + str(idx_iteration) + "_" + str(moat_i), lowBound=0, cat='Continuous')

    def calc_distance(self, city1, city2):
        """Calculates the distance from one city to another."""
        distance = math.sqrt(((city1[0] - city2[0]) ** 2) + ((city1[1] - city2[1]) ** 2))
        return distance

    def add_constraints_Y(self, S_s, iteration, G):
        """Adds constraints for the current iteration while keeping the constraints from old tours as well:
           The distance from one city i to another city j <= distance(i, j)
           In addition:
                for S_x in S_s
                    add constraint: r_i + r_j + Σ(Y_s) <= D(i,j)
                                    i ∈ S_i
                                    j ∉ S_i
        """
        for city_i in range(self.N):
            for city_j in range(city_i + 1, self.N):
                self.dual_[iteration] += self.radii_[iteration]["r_" + str(city_i)] \
                                         + self.radii_[iteration]["r_" + str(city_j)] \
                                         <= self.calc_distance(G[city_i], G[city_j])
                
        for idx, S_x in enumerate(S_s):
            for idx_subtour, subtour in enumerate(S_x):
                for idx_city_i, city_i in enumerate(subtour):
                    for idx_city_j in range(idx_subtour + 1, len(S_x)):
                        for city_j in S_x[idx_city_j]:
                            temp = 0
                            for idx_iteration_2, S_x_ in enumerate(S_s):
                                for idx_subtour_, subtour_ in enumerate(S_x_):
                                    if city_i in subtour_ and city_j in subtour_:
                                        break
                                    elif city_i in subtour_ or city_j in subtour_:
                                        temp += self.Ys_[iteration]["Ys_tour" + str(idx_iteration_2) + "_" + str(idx_subtour_)]
                            self.dual_[iteration] += (self.radii_[iteration]["r_" + str(city_i)]
                                                  + self.radii_[iteration]["r_" + str(city_j)]
                                                  + temp <= self.calc_distance(G[city_i], G[city_j]))
