import pytest
from triangle_class import Triangle, IncorrectTriangleSides

def test_equilateral():
    t = Triangle(5, 5, 5)
    assert t.triangle_type() == "equilateral"
    assert t.perimeter() == 15

def test_isosceles():
    t1 = Triangle(5, 5, 8)
    t2 = Triangle(5, 8, 5)
    t3 = Triangle(8, 5, 5)
    assert t1.triangle_type() == "isosceles"
    assert t2.triangle_type() == "isosceles"
    assert t3.triangle_type() == "isosceles"
    assert t1.perimeter() == 18

def test_nonequilateral():
    t = Triangle(3, 4, 5)
    assert t.triangle_type() == "nonequilateral"
    assert t.perimeter() == 12

def test_negative_sides():
    with pytest.raises(IncorrectTriangleSides):
        Triangle(-1, 2, 3)

def test_zero_sides():
    with pytest.raises(IncorrectTriangleSides):
        Triangle(0, 2, 3)

def test_invalid_sides():
    with pytest.raises(IncorrectTriangleSides):
        Triangle(1, 2, 10)
        