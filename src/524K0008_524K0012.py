"""Menu-driven interface for the Discrete Structures midterm."""

import importlib

_t1 = importlib.import_module("524K0008_524K0012_1")
_t2 = importlib.import_module("524K0008_524K0012_2")
_t3 = importlib.import_module("524K0008_524K0012_3")

run_task1_demo = _t1.run_task1_demo
run_task2_demo = _t2.run_task2_demo
run_task3_demo = _t3.run_task3_demo


def main() -> None:
    while True:
        print("\nDISCRETE STRUCTURES MIDTERM")
        print("1. Task 1 - Truth table")
        print("2. Task 2 - Predicate logic over data")
        print("3. Task 3 - RSA cryptosystem")
        print("0. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            run_task1_demo()
        elif choice == "2":
            run_task2_demo()
        elif choice == "3":
            run_task3_demo()
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid option. Please choose 0, 1, 2, or 3.")


if __name__ == "__main__":
    main()
