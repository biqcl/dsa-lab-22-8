class IncorrectTriangleSides(Exception):
    pass

def get_triangle_type(a, b, c):
    """
    Определяет тип треугольника по длинам его сторон.
    
    Аргументы:
        a, b, c (int или float): длины сторон треугольника
        
    Возвращает:
        str: тип треугольника ("equilateral", "isosceles", "nonequilateral")
        
    Выбрасывает:
        IncorrectTriangleSides: если стороны некорректны (не могут образовать треугольник)
    """
    # Проверка на корректность сторон
    if not (a > 0 and b > 0 and c > 0):
        raise IncorrectTriangleSides("Стороны должны быть положительными")
    if not (a + b > c and a + c > b and b + c > a):
        raise IncorrectTriangleSides("Сумма любых двух сторон должна быть больше третьей")
    
    # Определение типа треугольника
    if a == b == c:
        return "equilateral"
    elif a == b or a == c or b == c:
        return "isosceles"
    else:
        return "nonequilateral"
    