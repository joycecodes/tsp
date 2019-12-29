from PIL import Image, ImageDraw, ImageFont
import pulp
import math
import numpy as np
# from graph import Graph
import collections
import random
import primal
import dual


if __name__ == "__main__":
    def dist(p1, p2):  # takes tuple
        # calculates distance between two cities
        distance = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))
        return distance

    w, h = 1024, 512
    data = np.zeros((h, w, 3), dtype=np.uint8)
    for i in range(0, 500):
        for j in range(0, 1024):
            data[i, j] = [100, 100, 100]

    img = Image.fromarray(data, 'RGB')
    draw = ImageDraw.Draw(img)

    # Generates coordinates
    random.seed()
    N = random.randint(40, 50)
    coord = []

    for i in range(N):
        x, y  = random.randint(200, 900), random.randint(200, 400)
        coord.append((x, y))

    # this is basic graph
    G = {}
    for i in range(N):
        G[i] = coord[i]

    font = ImageFont.truetype("/tsplib/Arial.ttf", 12)

    """
        # filepath = "C:/Users/domed/Desktop/network-art/tsplib/test.txt"
    #[(72,131),(125,100),(125,162),(325,100),(325,162),(378,131)]
    with open(filepath) as fp:
        for cnt, line in enumerate(fp):
            s = line.split()
            idx, x, y = s
            coord.append((int(x),int(y)))
            # print("Line {}: {}".format(cnt, line))
            N+=1
    """

    # Gives you the distances from vtx i to vtx j
    dist_xy = {}
    for i in range(N):
        for j in range(i + 1, N):
            dist_xy[(i, j)] = dist(coord[i], coord[j])

    moats = []

    fin_radii = []
    control = []

    finished = False
    count = 0

    p = primal.prim([], N, [], [])    #rakes X_, N, S_s, primal
    d = dual.dual([], [], [], N)         # Ys, dual, radii_

    #   This creates the route, using int LP, denoted by the black lines
    while not finished:
        print("_______________________________________________")
        print(count)
        primal_cur = pulp.LpProblem("THIS IS NEW", pulp.LpMinimize)
        p.primal_.append(primal_cur)

        # Objective function:
        p.create_X(count)
        p.primal_[count] += pulp.lpSum(
            p.X_[count][str(i) + "_" + str(j)] * dist_xy[(i, j)] for i in range(N) for j in range(i + 1, N)), "Z"
        # print("OBJECTIVE: ", primal_[count].objective)

        # Constraints
        p.add_constraints(count, p.S_s)

        # Solves the LP
        #print(primal_[count])
        p.primal_[count].solve()

        # Sets the variables in dict X_count, either 1 or 0; tells you whether or not you take the path (i,j)
        for variable in p.primal_[count].variables():
            p.X_[count][str(variable.name)] = int(variable.varValue)

        S_x = p.create_S_x(count)
        print("new_S_x: ", S_x)
        p.add_to_S_s(S_x)
        print("S_s: ", p.S_s)

        # Dual LP
        if len(S_x) > 1:
            # Creates a list of radii at each run
            d.radii_.append({})
            for i in range(N):
                d.radii_[count]["r_" + str(i)] = pulp.LpVariable("r_" + str(i), lowBound=0, cat='Continuous')

            # create Ys_
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

            # ADDS CONSTRAINTS
            d.add_constraints_Y(p.S_s, count, G)
            d.dual_[count].solve()

        if len(S_x) == 1:
            print(pulp.value(d.dual_[count-1].objective))
            print(pulp.value(p.primal_[-1].objective))

            Y = [[] for i in range(count)]
            R = {}

            for variable in d.dual_[-1].variables():
                if variable.name[0] == "Y":
                    throw, tour, idx = variable.name.split("_")
                    tour = int(tour[4:])
                    Y[tour].append((idx, variable.varValue)) #ex: Y[tour][(Ys: Ys_val)]
                else:
                    R[variable.name] = variable.varValue
            print(Y)
            print(R)

            result = []

            for i in range(count):
                result.append({})
                for j in range(len(p.S_s[i])):
                    for city in p.S_s[i][j]:
                        moat = Y[i][j][-1] #gives you the width of moat (Ys_j)
                        if i == 0:
                            result[i]["r_"+ str(city)] = moat + R["r_" + str(city)]
                        else:
                            result[i]["r_" + str(city)] = result[i-1]["r_" + str(city)] + moat
            #print(result)
            result = result[::-1]

            key = 0
            for m in range(count):
                ans = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                key+=15
                draw.ellipse([10, key, 18, key+8], fill=ans)
                draw.text((23, key), str(m), (0, 0, 0), font=font)
                for i in range(N):
                    x, y = G[i]
                    moat = result[m]["r_" + str(i)]
                    draw.ellipse([x - moat, y - moat, x + moat, y + moat], fill=ans)

            ans = (random.randint(0, 200), random.randint(0, 255), random.randint(50, 255))

            for i in range(N):
                x, y = G[i]
                c = R["r_" + str(i)]
                draw.ellipse([x - c, y - c, x + c, y + c], fill=ans)

            for i in range(N):
                x, y = G[i]
                c = 2
                draw.ellipse([x - c, y - c, x + c, y + c], fill=(0, 0, 0))

            ##########

            finished = True
            ans = {}
            for variable in p.primal_[-1].variables():
                ans[str(variable.name)] = int(variable.varValue)
            for path in ans:
                if ans[path]:
                    xs = path.split("_")
                    x_1, y_1 = G[int(xs[0])]
                    x_2, y_2 = G[int(xs[1])]
                    draw.line([x_1, y_1, x_2, y_2], fill = (0, 0, 0), width = 1)
            for idx, v in enumerate(G):
                x, y = G[v]
                draw.text((x + 5, y + 2), str(idx), (0, 0, 0), font = font)
            # print(primal_[count].objective)
        count += 1

    img.save('my.png')
    img.show()
