import sys
sys.path.append('..')
import main_tsp
import pytest

def test_city_has_two_paths():
    """Each city should have only two paths: one to enter and the other to exit."""
    p, d, _, _, pulp = main_tsp.solve()

    cities = {}
    compare = p.X_[-1]
    ans = True
    for city in compare:
        start, end = city.split("_")
        if compare[city]:
            cities[start] = cities.get(start, 0) + 1
            cities[end] = cities.get(end, 0) + 1
    for city in cities:
        if cities[city] != 2:
            ans = False
    assert ans == True

def test_dual_less_than_primal():
    """We know that the dual LP is accurate if the size of all cities is less than or equal to
       the length of the tour."""
    p, d, _, _, pulp = main_tsp.solve()
    dual = pulp.value(d.dual_[-1].objective)
    primal = pulp.value(p.primal_[-1].objective)
    assert dual <= primal

def test_num_of_cities_matches_random_generator():
    """This test makes sure that the number of cities in the list matches the number generated."""
    _, _, N, cities, _ = main_tsp.solve()
    assert N == len(cities)

@pytest.mark.parametrize("input1, input2, output1",[((0, 0), (0, 0), 0), ((50, 100), (50, 50), 50), ((10, 50), (0, 50), 10)])
def test_calc_distance(input1, input2, output1):
    """This checks that the method to calculate distance given two points is correct."""
    _, d, _, _, _ = main_tsp.solve()
    assert d.calc_distance(input1, input2) == output1

