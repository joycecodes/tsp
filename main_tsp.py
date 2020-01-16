from PIL import Image, ImageDraw, ImageFont
import pulp
import math
import numpy as np
import random
import primal
import dual

coordinates = []

def create_number_of_cities(cities, is_random=None):
    """Generates a random number of cities and its coordinates"""
    if not is_random:
        random.seed()
        N = random.randint(40, 50)
    else:
        N = is_random
    for city in range(N):
        x, y = random.randint(200, 900), random.randint(200, 400)
        coordinates.append((x, y))
        cities[city] = coordinates[city]
    return N


def solve(visualize=False):
    # Creates a window of size w x h
    w, h = 1024, 512
    data = np.zeros((h, w, 3), dtype=np.uint8)
    for i in range(0, 512):
        for j in range(0, 1024):
            data[i, j] = [100, 100, 100]

    img = Image.fromarray(data, 'RGB')
    draw = ImageDraw.Draw(img)

    cities = {}
    N = create_number_of_cities(cities)
    font = ImageFont.truetype("fonts/Arial.ttf", 11)
    finished = False
    iteration_count = 0

    # Creates the primal and dual objects
    p = primal.Primal([], N, [], [])
    d = dual.Dual([], [], [], N)

    while not finished:
        print("_______________________________________________")
        print(iteration_count)
        primal_cur = pulp.LpProblem("primal", pulp.LpMinimize)
        p.primal_.append(primal_cur)

        # Objective function:
        p.create_X(iteration_count)
        p.primal_[iteration_count] += pulp.lpSum(
            p.X_[iteration_count][str(i) + "_" + str(j)] * d.calc_distance(cities[i], cities[j]) for i in range(N) for j
            in range(i + 1, N)), "Z"

        # Constraints
        p.add_constraints(iteration_count)

        # Solves the LP
        p.primal_[iteration_count].solve()

        # Sets the variables in X_[iteration_count], either 1 or 0; tells you whether or not you take the path (i,j)
        for variable in p.primal_[iteration_count].variables():
            p.X_[iteration_count][str(variable.name)] = int(variable.varValue)

        S_x = p.create_S_x(iteration_count)
        p.add_to_S_s(S_x)
        print("new S_x: ", S_x)
        print("S_s: ", p.S_s)

        # Dual LP, this only runs if there is at least one subtour
        if len(S_x) > 1:
            d.radii_.append({})
            for city_i in range(N):
                d.radii_[iteration_count]["r_" + str(city_i)] = pulp.LpVariable("r_" + str(city_i), lowBound=0, cat='Continuous')

            # Creates Ys/moat for each subtour
            d.create_Ys(p.S_s, iteration_count)

            dual_cur = pulp.LpProblem("the dual", pulp.LpMaximize)
            d.dual_.append(dual_cur)

            # Objective function:
            temp = pulp.LpAffineExpression()
            for city_i in range(N):
                temp += pulp.lpSum(2 * d.radii_[iteration_count]["r_" + str(city_i)])
            for iteration_idx, S_x in enumerate(p.S_s):
                for subtour in range(len(S_x)):
                    temp += pulp.lpSum(2 * d.Ys_[iteration_count]["Ys_tour" + str(iteration_idx) + "_" + str(subtour)])
            d.dual_[iteration_count] += temp, "Z"

            d.add_constraints_Y(p.S_s, iteration_count, cities)
            d.dual_[iteration_count].solve()

        if len(S_x) == 1:
            # This stores the moats from the final iteration and then adds up the moat sizes so it can be used to
            # draw the final image
            Ys = [[] for i in range(iteration_count)]
            Radii = {}

            for variable in d.dual_[-1].variables():
                if variable.name[0] == "Y":
                    throwaway, tour, idx = variable.name.split("_")
                    tour = int(tour[4:])
                    Ys[tour].append((idx, variable.varValue))
                else:
                    Radii[variable.name] = variable.varValue

            fin_moats_for_each_city = []
            for iteration in range(iteration_count):
                fin_moats_for_each_city.append({})
                for subtour in range(len(p.S_s[iteration])):
                    for city in p.S_s[iteration][subtour]:
                        moat = Ys[iteration][subtour][-1]
                        if iteration == 0:
                            fin_moats_for_each_city[iteration]["r_" + str(city)] = moat + Radii["r_" + str(city)]
                        else:
                            fin_moats_for_each_city[iteration]["r_" + str(city)] = fin_moats_for_each_city[iteration - 1][
                                                                                   "r_" + str(city)] + moat
            fin_moats_for_each_city = fin_moats_for_each_city[::-1]

            # This draws the legend identifying which iteration a moat was created by its color
            # and also draws the moats
            legend_y_coord = 0
            for city in range(iteration_count):
                moat_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                legend_y_coord += 15
                draw.ellipse([10, legend_y_coord, 18, legend_y_coord + 8], fill=moat_color)

                draw.text((23, legend_y_coord), str(city), (0, 0, 0), font=font)
                for city_i in range(N):
                    x, y = cities[city_i]
                    moat = fin_moats_for_each_city[city]["r_" + str(city_i)]
                    draw.ellipse([x - moat, y - moat, x + moat, y + moat], fill=moat_color)

            control_zone_color = (random.randint(0, 200), random.randint(0, 255), random.randint(50, 255))
            for city in range(N):
                x, y = cities[city]
                radius = Radii["r_" + str(city)]
                draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=control_zone_color)

            finished = True

            # Draws the connecting tour for the primal ILP
            connecting_tour = {}
            for variable in p.primal_[-1].variables():
                connecting_tour[str(variable.name)] = int(variable.varValue)
            for path in connecting_tour:
                if connecting_tour[path]:
                    xs = path.split("_")
                    x_1, y_1 = cities[int(xs[0])]
                    x_2, y_2 = cities[int(xs[1])]
                    draw.line([x_1, y_1, x_2, y_2], fill=(0, 0, 0), width=1)
            for idx, city in enumerate(cities):
                x, y = cities[city]
                radius = 2
                draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(0, 0, 0))
                draw.text((x + 5, y + 2), str(idx), (0, 0, 0), font=font)
        iteration_count += 1
    if visualize:
        img.save('my.png')
        img.show()

    return p, d, N, cities, pulp


if __name__=='__main__':
    solve(visualize=True)