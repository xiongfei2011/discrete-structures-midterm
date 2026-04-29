"""Menu-driven interface for the Discrete Structures midterm."""

from task1_logic import run_task1_demo


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
            print("Task 2 has not been implemented yet.")
        elif choice == "3":
            print("Task 3 has not been implemented yet.")
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid option. Please choose 0, 1, 2, or 3.")


if __name__ == "__main__":
    main()
