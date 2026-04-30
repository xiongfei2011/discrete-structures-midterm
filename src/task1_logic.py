from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, Iterable, List, Sequence, Tuple


OPERATORS = {"~", "&", "|", "^", ">", "="}
PRECEDENCE = {
    "~": 5,
    "&": 4,
    "^": 3,
    "|": 2,
    ">": 1,
    "=": 0,
}
RIGHT_ASSOCIATIVE = {"~", ">", "="}


@dataclass(frozen=True)
class TruthTable:
    expression: str
    variables: Tuple[str, ...]
    rows: Tuple[Tuple[Dict[str, bool], bool], ...]


def _is_variable(token: str) -> bool: 
    return bool(token) and (token[0].isalpha() or token[0] == "_")


def tokenize(infix: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    while i < len(infix):
        ch = infix[i]
        if ch.isspace():
            i += 1
            continue
        if ch in OPERATORS or ch in "()":
            tokens.append(ch)
            i += 1
            continue
        if ch.isalpha() or ch == "_":
            start = i
            i += 1
            while i < len(infix) and (infix[i].isalnum() or infix[i] == "_"):
                i += 1
            tokens.append(infix[start:i])
            continue
        raise ValueError(f"Invalid character {ch!r} at position {i}.")
    return tokens


def Infix2Postfix(Infix: str) -> str:
    output: List[str] = []
    stack: List[str] = []

    for token in tokenize(Infix):
        if _is_variable(token):
            output.append(token)
        elif token == "(":
            stack.append(token)
        elif token == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses: missing '('.")
            stack.pop()
        elif token in OPERATORS:
            while stack and stack[-1] in OPERATORS:
                top = stack[-1]
                higher = PRECEDENCE[top] > PRECEDENCE[token]
                same_left = (
                    PRECEDENCE[top] == PRECEDENCE[token]
                    and token not in RIGHT_ASSOCIATIVE
                )
                if higher or same_left: 
                    output.append(stack.pop())
                else:
                    break
            stack.append(token)
        else:
            raise ValueError(f"Unknown token {token!r}.")

    while stack:
        top = stack.pop()
        if top in "()":
            raise ValueError("Mismatched parentheses.")
        output.append(top)

    return " ".join(output)


def _postfix_tokens(postfix: str | Sequence[str]) -> List[str]:
    if isinstance(postfix, str):
        return postfix.split()
    return list(postfix)


def variables_from_postfix(postfix: str | Sequence[str]) -> Tuple[str, ...]:
    variables = sorted({token for token in _postfix_tokens(postfix) if _is_variable(token)})
    return tuple(variables)


def _apply_operator(operator: str, stack: List[bool]) -> None:
    if operator == "~":
        if not stack:
            raise ValueError("Operator '~' is missing one operand.")
        stack.append(not stack.pop())
        return

    if len(stack) < 2:
        raise ValueError(f"Operator {operator!r} is missing operands.")
    right = stack.pop()
    left = stack.pop()

    if operator == "&":
        stack.append(left and right)
    elif operator == "|":
        stack.append(left or right)
    elif operator == "^":
        stack.append(left != right)
    elif operator == ">":
        stack.append((not left) or right)
    elif operator == "=":
        stack.append(left == right)
    else:
        raise ValueError(f"Unknown operator {operator!r}.")


def evaluate_postfix(postfix: str | Sequence[str], values: Dict[str, bool]) -> bool: 
    stack: List[bool] = []
    for token in _postfix_tokens(postfix):
        if _is_variable(token):
            if token not in values:
                raise ValueError(f"No truth value was provided for {token!r}.")
            stack.append(values[token])
        elif token in OPERATORS:
            _apply_operator(token, stack)
        else:
            raise ValueError(f"Unknown postfix token {token!r}.")

    if len(stack) != 1:
        raise ValueError("Invalid postfix expression.")
    return stack[0]


def Postfix2Truthtable(Postfix: str) -> TruthTable:
    variables = variables_from_postfix(Postfix)
    rows = []
    for values in product([False, True], repeat=len(variables)):
        assignment = dict(zip(variables, values))
        result = evaluate_postfix(Postfix, assignment)
        rows.append((assignment, result))
    return TruthTable(Postfix, variables, tuple(rows))


def Infix2Truthtable(infix: str) -> TruthTable:
    return Postfix2Truthtable(Infix2Postfix(infix))


def GetDNF(truth_table: TruthTable) -> str: 
    terms: List[str] = []
    for assignment, result in truth_table.rows:
        if not result:
            continue
        literals = []
        for variable in truth_table.variables:
            literals.append(variable if assignment[variable] else f"~{variable}")
        terms.append("(" + " & ".join(literals) + ")")

    if not terms: 
        return "False"
    if len(terms) == 2 ** len(truth_table.variables):
        return "True"
    return " | ".join(terms)


def CheckEquivalence(Infix1: str, Infix2: str) -> bool:
    postfix1 = Infix2Postfix(Infix1)
    postfix2 = Infix2Postfix(Infix2)
    variables = sorted(set(variables_from_postfix(postfix1)) | set(variables_from_postfix(postfix2)))

    for values in product([False, True], repeat=len(variables)):
        assignment = dict(zip(variables, values))
        if evaluate_postfix(postfix1, assignment) != evaluate_postfix(postfix2, assignment):
            return False
    return True


def format_truth_table(table: TruthTable) -> str:
    headers = list(table.variables) + ["Result"]
    widths = {header: max(len(header), 1) for header in headers}
    rows = []
    for assignment, result in table.rows:
        display_row = {variable: _tf(assignment[variable]) for variable in table.variables}
        display_row["Result"] = _tf(result)
        rows.append(display_row)
        for header, value in display_row.items():
            widths[header] = max(widths[header], len(value))

    line = " | ".join(header.ljust(widths[header]) for header in headers)
    separator = "-+-".join("-" * widths[header] for header in headers)
    body = [
        " | ".join(row[header].ljust(widths[header]) for header in headers)
        for row in rows
    ]
    return "\n".join([line, separator, *body])


def _tf(value: bool) -> str:
    return "T" if value else "F"


TASK1_TESTCASES = [
    "R|(P&Q)",
    "~P|(Q&R)>R",
    "P|(R&Q)",
    "(P>Q)&(Q>R)",
    "(P|~Q)>~P=(P|(~Q))>~P",
]

EQUIVALENCE_TESTCASES = [
    ("P>Q", "~P|Q"),
    ("P=Q", "(P&Q)|(~P&~Q)"),
    ("P^Q", "(P|Q)&~(P&Q)"),
    ("P&(Q|R)", "(P&Q)|(P&R)"),
    ("P|Q", "P&Q"),
]


def run_task1_demo() -> None:
    print("TASK 1 - TRUTH TABLE")
    print("=" * 60)
    for index, infix in enumerate(TASK1_TESTCASES, start=1):
        postfix = Infix2Postfix(infix)
        table = Postfix2Truthtable(postfix)
        print(f"\nTestcase {index}: {infix}")
        print(f"Postfix: {postfix}")
        print(format_truth_table(table))
        print(f"DNF: {GetDNF(table)}")

    print("\nEQUIVALENCE TESTS")
    print("=" * 60)
    for index, (left, right) in enumerate(EQUIVALENCE_TESTCASES, start=1):
        result = CheckEquivalence(left, right)
        print(f"{index}. {left}  <=>  {right}: {result}")


if __name__ == "__main__":
    run_task1_demo()
