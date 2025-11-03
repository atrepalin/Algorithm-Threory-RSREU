import keyboard
import pandas as pd
import numpy as np

def select_option(options, title="Выберите вариант:"):
    current_selection = 0

    def print_menu():
        print('\033c', end='')
        print(title)
        for i, option in enumerate(options):
            if i == current_selection:
                print(f"\033[0;32m> {option}\033[0m")
            else:
                print(f"  {option}")

    print_menu()

    while True:
        event = keyboard.read_event(True)
        if event.event_type == "down":
            if event.name == "up":
                current_selection = (current_selection - 1) % len(options)
            elif event.name == "down":
                current_selection = (current_selection + 1) % len(options)
            elif event.name == "enter":
                break
            print_menu()

    print('\033c', end='')

    return current_selection

def main():
    name = input("Введите название нечеткого свойства: ")
    elements = input("Введите элементы через запятую: ").split(',')
    elements = [e.strip() for e in elements]

    scale = [
        "1 — отсутствие преимущества",
        "2 — промежуточное между 1 и 3",
        "3 — слабое преимущество",
        "4 — промежуточное между 3 и 5",
        "5 — существенное преимущество",
        "6 — промежуточное между 5 и 7",
        "7 — явное преимущество",
        "8 — промежуточное между 7 и 9",
        "9 — абсолютное преимущество"
    ]

    n = len(elements)
    matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            value = select_option(scale, f"Сравнение: {elements[i]} vs {elements[j]}") + 1

            direction = select_option(
                [f"{elements[i]} предпочтительнее {elements[j]}",
                 f"{elements[j]} предпочтительнее {elements[i]}"],
                "Укажите направление сравнения:"
            )

            if direction == 0:
                matrix[i][j] = value
                matrix[j][i] = 1 / value
            else:
                matrix[i][j] = 1 / value
                matrix[j][i] = value

    df = pd.DataFrame(matrix, index=elements, columns=elements)
    print(f"Матрица Саати для нечеткого свойства: {name}")
    print(df)

    mtx = np.array(matrix)
    col_sums = mtx.sum(axis=0)

    mu = []
    for k in range(n):
        ratios = mtx[k, :] / col_sums
        mu_k = np.mean(ratios)
        mu.append(mu_k)

    df_mu = pd.DataFrame({
        "Степень принадлежности": mu
    }, index=elements)

    print("\nФункция принадлежности (μ) для каждого элемента:")
    print(df_mu)

if __name__ == "__main__":
    main()
