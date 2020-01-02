from PIL import Image, ImageDraw, ImageFont
import pulp
import math
import numpy as np
import collections
import random
import primal
import dual

if __name__ == "__main__":
    def dist(p1, p2):
        # Calculates distance between two cities
        distance = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))
        return distance

    w, h = 1024, 512
    data = np.zeros((h, w, 3), dtype=np.uint8)
    for i in range(0, 512):
        for j in range(0, 1024):
            data[i, j] = [100, 100, 100]

    img = Image.fromarray(data, 'RGB')
    draw = ImageDraw.Draw(img)

    # Generates a random number of cities
    random.seed()
    N = random.randint(40, 50)
    coord = []

    # This contains cities and its coordinates
    G = {}
    for i in range(N):
        x, y = random.randint(200, 900), random.randint(200, 400)
        coord.append((x, y))
        G[i] = coord[i]

    font = ImageFont.truetype("fonts/Arial.ttf", 11)

    # Gives you the distance from vtx i to vtx j
    dist_xy = {}
    for i in range(N):
        for j in range(i + 1, N):
            dist_xy[(i, j)] = dist(coord[i], coord[j])

    finished = False
    count = 0

    p = primal.primal([], N, [], [])    # (X_, N, S_s, primal)
    d = dual.dual([], [], [], N)        # (Ys, dual, radii_, N)

    # This creates the route, using ILP, denoted by the black lines
    while not finished:
        print("_______________________________________________")
        print(count)
        primal_cur = pulp.LpProblem("primal", pulp.LpMinimize)
        p.primal_.append(primal_cur)

        # Objective function:
        p.create_X(count)
        p.primal_[count] += pulp.lpSum(
            p.X_[count][str(i) + "_" + str(j)] * dist_xy[(i, j)] for i in range(N) for j in range(i + 1, N)), "Z"

        # Constraints
        p.add_constraints(count, p.S_s)

        # Solves the LP
        p.primal_[count].solve()

        # Sets the variables in X_[count], either 1 or 0; tells you whether or not you take the path (i,j)
        for variable in p.primal_[count].variables():
            p.X_[count][str(variable.name)] = int(variable.varValue)

        S_x = p.create_S_x(count)
        p.add_to_S_s(S_x)
        print("new S_x: ", S_x)
        print("S_s: ", p.S_s)

        # Dual LP, this only runs if there is at least one subtour
        if len(S_x) > 1:
            # Creates variables for each city's radius
            d.radii_.append({})
            for i in range(N):
                d.radii_[count]["r_" + str(i)] = pulp.LpVariable("r_" + str(i), lowBound=0, cat='Continuous')

            # Creates Ys for each subtour
            d.create_Ys(p.S_s, count)

            # Objective function:
            dual_cur = pulp.LpProblem("the dual", pulp.LpMaximize)
            d.dual_.append(dual_cur)

            temp = pulp.LpAffineExpression()
            for i in range(N):
                temp += pulp.lpSum(2 * d.radii_[count]["r_" + str(i)])
            for idx, S_x in enumerate(p.S_s):
                for i in range(len(S_x)):
                    temp += pulp.lpSum(2 * d.Ys_[count]["Ys_tour" + str(idx) + "_" + str(i)])
            d.dual_[count] += temp, "Z"

            # Adds constraints from previous and current iteration
            d.add_constraints_Y(p.S_s, count, G)
            d.dual_[count].solve()
        
        # Draws the final image
        if len(S_x) == 1:
            # To verify that the dual is correct, it should be <= to the primal
            print(pulp.value(d.dual_[count-1].objective))
            print(pulp.value(p.primal_[-1].objective))

            Ys = [[] for i in range(count)]  # Stores the moats from the final iteration
            Radii = {}  # Width of each city

            for variable in d.dual_[-1].variables():
                if variable.name[0] == "Y":
                    throw, tour, idx = variable.name.split("_")
                    tour = int(tour[4:])
                    Ys[tour].append((idx, variable.varValue))  # ex: Ys[tour][(Ys_idx, Ys_val)]
                else:
                    Radii[variable.name] = variable.varValue
            
            fin_moats_for_each_city = []  # Adds up the moat sizes so it can be used to draw the image
            for i in range(count):
                fin_moats_for_each_city.append({})
                for j in range(len(p.S_s[i])):
                    for city in p.S_s[i][j]:
                        moat = Ys[i][j][-1]  # Gives you the width of moat (Ys_j)
                        if i == 0:
                            fin_moats_for_each_city[i]["r_" + str(city)] = moat + Radii["r_" + str(city)]
                        else:
                            fin_moats_for_each_city[i]["r_" + str(city)] = fin_moats_for_each_city[i-1]["r_" + str(city)] + moat
            fin_moats_for_each_city = fin_moats_for_each_city[::-1]
            
            # This draws the legend identifying which iteration a moat occurred corresponding to the color
            # Also draws the moats
            legend_y_coord = 0
            for city in range(count):
                moat_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                legend_y_coord += 15
                draw.ellipse([10, legend_y_coord, 18, legend_y_coord+8], fill=moat_color)
                draw.text((23, legend_y_coord), str(city), (0, 0, 0), font=font)
                for i in range(N):
                    x, y = G[i]
                    moat = fin_moats_for_each_city[city]["r_" + str(i)]
                    draw.ellipse([x - moat, y - moat, x + moat, y + moat], fill=moat_color)

            control_zone_color = (random.randint(0, 200), random.randint(0, 255), random.randint(50, 255))
            
            # Draws the radius of the control zone
            for i in range(N):
                x, y = G[i]
                c = Radii["r_" + str(i)]
                draw.ellipse([x - c, y - c, x + c, y + c], fill=control_zone_color)
                
            # Draws a dot for each city
            for i in range(N):
                x, y = G[i]
                c = 2
                draw.ellipse([x - c, y - c, x + c, y + c], fill=(0, 0, 0))
        
            finished = True

            # Draws the connecting tour
            connecting_tour = {}
            for variable in p.primal_[-1].variables():
                connecting_tour[str(variable.name)] = int(variable.varValue)
            for path in connecting_tour:
                if connecting_tour[path]:
                    xs = path.split("_")
                    x_1, y_1 = G[int(xs[0])]
                    x_2, y_2 = G[int(xs[1])]
                    draw.line([x_1, y_1, x_2, y_2], fill=(0, 0, 0), width=1)
            for idx, city in enumerate(G):
                x, y = G[city]
                draw.text((x + 5, y + 2), str(idx), (0, 0, 0), font=font)
            # print(primal_[count].objective)
        count += 1

    img.save('my.png')
    img.show()
