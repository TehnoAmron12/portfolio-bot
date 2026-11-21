menu = [
    ("Цезарь", 350, 200),
    ("Бургер", 500, 450),
    ("Пицца Маргарита", 2500, 450),
    ("Бургер Классический", 1800, 320),
    ("Картофель фри", 800, 150)
]
print("Первое блюдо:", menu)
print("Всё меню:", menu)

students = [('Alice', 22), ('Bob', 20), ('Charlie', 25)]
sorted_students = sorted(students, key=lambda x: x)
print("Отсортированные студенты:", sorted_students)

cities = {
    (1, 2): "-",
    (3, 4): "+",
    (40.7128, -74.0060): "New York",
    (43.2220, 76.8512): "Almaty",
    (51.5074, -0.1278): "London"
}

for coords, city in cities.items():
    print(coords, city)
