from __future__ import annotations

import csv
import math
import random
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "524K0008_524K0012.csv"
SUBJECTS = ("Math", "CS", "Eng")
Student = Dict[str, object]


def create_dataset(path: Path = DATA_PATH, record_count: int = 1000) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2026)
    first_names = [
        "An",
        "Binh",
        "Chi",
        "Dung",
        "Giang",
        "Hieu",
        "Khanh",
        "Lan",
        "Minh",
        "Nhi",
        "Phong",
        "Quang",
        "Thao",
        "Trang",
        "Vy",
    ]
    last_names = [
        "Nguyen",
        "Tran",
        "Le",
        "Pham",
        "Hoang",
        "Phan",
        "Vu",
        "Dang",
        "Bui",
        "Do",
    ]
    start_birth = date(2003, 1, 1)

    rows: List[Dict[str, object]] = []
    for index in range(record_count):
        student_id = f"SV{index + 1:04d}"
        student_name = f"{rng.choice(last_names)} {rng.choice(first_names)}"
        birth = start_birth + timedelta(days=rng.randint(0, 1460))
        rows.append(
            {
                "StudentID": student_id,
                "StudentName": student_name,
                "DayOfBirth": birth.isoformat(),
                "Math": round(rng.uniform(0, 10), 1),
                "CS": round(rng.uniform(0, 10), 1),
                "Eng": round(rng.uniform(0, 10), 1),
            }
        )

    noisy_indexes = rng.sample(range(record_count), 60)
    noisy_values = ["", "NULL", -3.5, 12.2, "abc"]
    for position, row_index in enumerate(noisy_indexes):
        subject = SUBJECTS[position % len(SUBJECTS)]
        rows[row_index][subject] = noisy_values[position % len(noisy_values)]
        if position % 10 == 0:
            rows[row_index]["DayOfBirth"] = "invalid-date"

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["StudentID", "StudentName", "DayOfBirth", *SUBJECTS],
        )
        writer.writeheader()
        writer.writerows(rows)

    return path


def _clean_score(value: object) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return math.nan
    if 0 <= score <= 10:
        return score
    return math.nan


def _has_score(student: Student, subject: str) -> bool:
    value = student.get(subject)
    return isinstance(value, float) and not math.isnan(value)


def clean_student(raw: Dict[str, str]) -> Student:
    student: Student = {
        "StudentID": raw["StudentID"],
        "StudentName": raw["StudentName"],
        "DayOfBirth": raw["DayOfBirth"],
    }
    for subject in SUBJECTS:
        student[subject] = _clean_score(raw.get(subject))
    return student


def load_students(path: Path = DATA_PATH) -> List[Student]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return [clean_student(row) for row in csv.DictReader(file)]


def load_dataframe(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["DayOfBirth"] = pd.to_datetime(df["DayOfBirth"], errors="coerce")
    for subject in SUBJECTS:
        df[subject] = pd.to_numeric(df[subject], errors="coerce")
        df.loc[~df[subject].between(0, 10), subject] = np.nan
    return df


def is_passing(student: Student) -> bool:
    return all(_has_score(student, subject) and student[subject] >= 5 for subject in SUBJECTS)


def is_high_math(student: Student) -> bool:
    return _has_score(student, "Math") and student["Math"] >= 9


def is_struggling(student: Student) -> bool:
    return (
        _has_score(student, "Math")
        and _has_score(student, "CS")
        and student["Math"] < 6
        and student["CS"] < 6
    )


def improved_in_cs(student: Student) -> bool:
    return (
        _has_score(student, "Math")
        and _has_score(student, "CS")
        and student["CS"] > student["Math"]
    )


def all_students_passed_all_subjects(students: Iterable[Student]) -> bool:
    return all(is_passing(student) for student in students)


def all_students_have_math_higher_than_3(students: Iterable[Student]) -> bool:
    return all(_has_score(student, "Math") and student["Math"] > 3 for student in students)


def exists_high_math_student(students: Iterable[Student]) -> bool:
    return any(is_high_math(student) for student in students)


def exists_student_improved_in_cs(students: Iterable[Student]) -> bool:
    return any(improved_in_cs(student) for student in students)


def every_student_has_subject_above_6(students: Iterable[Student]) -> bool:
    return all(
        any(_has_score(student, subject) and student[subject] > 6 for subject in SUBJECTS)
        for student in students
    )


def every_low_math_student_has_subject_above_6(students: Iterable[Student]) -> bool:
    for student in students:
        low_math = _has_score(student, "Math") and student["Math"] < 6
        if low_math and not any(
            _has_score(student, subject) and student[subject] > 6 for subject in SUBJECTS
        ):
            return False
    return True


def vectorized_statements(df: pd.DataFrame) -> Dict[str, bool]:
    valid_scores = df[list(SUBJECTS)].notna()
    return {
        "All students passed all subjects": bool(((df[list(SUBJECTS)] >= 5) & valid_scores).all(axis=1).all()),
        "All students have a math score higher than 3": bool((df["Math"].notna() & (df["Math"] > 3)).all()),
        "There exists a student who scored above 9 in math": bool((df["Math"] >= 9).any()),
        "There exists a student who improved in CS over Math": bool((df["CS"].notna() & df["Math"].notna() & (df["CS"] > df["Math"])).any()),
        "For every student, there exists a subject in which they scored above 6": bool((df[list(SUBJECTS)] > 6).any(axis=1).all()),
        "For every student scoring below 6 in Math, there exists a subject where they scored above 6": bool((~(df["Math"].notna() & (df["Math"] < 6)) | (df[list(SUBJECTS)] > 6).any(axis=1)).all()), # Implication: If Math is below 6, then at least one subject must be above 6. Negation: There exists a student with Math < 6 and no subject > 6.
    }


LOOP_STATEMENTS: List[Tuple[str, Callable[[Iterable[Student]], bool], str]] = [
    (
        "All students passed all subjects",
        all_students_passed_all_subjects,
        "Negation: At least one student did not pass one or more subjects.",
    ),
    (
        "All students have a math score higher than 3",
        all_students_have_math_higher_than_3,
        "Negation: At least one student has Math <= 3 or an invalid Math score.",
    ),
    (
        "There exists a student who scored above 9 in math",
        exists_high_math_student,
        "Negation: No student has Math >= 9.",
    ),
    (
        "There exists a student who improved in CS over Math",
        exists_student_improved_in_cs,
        "Negation: Every student has CS <= Math or lacks a valid Math/CS score.",
    ),
    (
        "For every student, there exists a subject in which they scored above 6",
        every_student_has_subject_above_6,
        "Negation: At least one student has no subject score above 6.",
    ),
    (
        "For every student scoring below 6 in Math, there exists a subject where they scored above 6",
        every_low_math_student_has_subject_above_6,
        "Negation: At least one Math-below-6 student has no subject score above 6.",
    ),
]


def loop_statements(students: List[Student]) -> Dict[str, bool]:
    return {name: evaluator(students) for name, evaluator, _ in LOOP_STATEMENTS}


def measure_time(function: Callable[[], Dict[str, bool]], repeats: int = 100) -> Tuple[Dict[str, bool], float]:
    start = time.perf_counter()
    result: Dict[str, bool] = {}
    for _ in range(repeats):
        result = function()
    elapsed = time.perf_counter() - start
    return result, elapsed / repeats


def count_noisy_rows(df: pd.DataFrame) -> int:
    return int((df[list(SUBJECTS)].isna().any(axis=1) | df["DayOfBirth"].isna()).sum())


def run_task2_demo() -> None:
    create_dataset(DATA_PATH)
    students = load_students(DATA_PATH)
    df = load_dataframe(DATA_PATH)

    loop_results, loop_time = measure_time(lambda: loop_statements(students))
    vector_results, vector_time = measure_time(lambda: vectorized_statements(df))

    print("TASK 2 - QUANTIFIED REASONING OVER STUDENT DATA")
    print("=" * 70)
    print(f"Dataset: {DATA_PATH}")
    print(f"Total records: {len(students)}")
    print(f"Rows with missing/noisy data after cleaning: {count_noisy_rows(df)}")
    print("\nPredicates:")
    print("- is_passing(student): Math, CS, and Eng are all >= 5.")
    print("- is_high_math(student): Math is >= 9.")
    print("- is_struggling(student): Math and CS are both < 6.")
    print("- improved_in_cs(student): CS is greater than Math.")

    print("\nQuantified statements and negations:")
    for name, _, negation_text in LOOP_STATEMENTS:
        print(f"- {name}: {loop_results[name]}")
        print(f"  {negation_text} Value: {not loop_results[name]}")

    print("\nLoop vs vectorized check:")
    for name in loop_results:
        print(f"- {name}: loop={loop_results[name]}, vectorized={vector_results[name]}")

    print("\nAverage execution time over 100 runs:")
    print(f"- Naive loop approach: {loop_time:.8f} seconds/run")
    print(f"- Pandas vectorized approach: {vector_time:.8f} seconds/run")


if __name__ == "__main__":
    run_task2_demo()
