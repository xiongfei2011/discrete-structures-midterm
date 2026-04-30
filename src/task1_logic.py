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


@dataclass(frozen=True) #Helpful for immutability and easy printing, but not strictly necessary
class TruthTable:
    expression: str
    variables: Tuple[str, ...]
    rows: Tuple[Tuple[Dict[str, bool], bool], ...]


def _is_variable(token: str) -> bool: #Checks if the token is a valid variable name (starts with a letter or underscore, followed by alphanumeric characters or underscores)
    return bool(token) and (token[0].isalpha() or token[0] == "_")


def tokenize(infix: str) -> List[str]: #Splits an infix expression into variables, operators, and parentheses
    """Split an infix expression into variables, operators, and parentheses."""
    tokens: List[str] = []
    i = 0
    while i < len(infix):
        ch = infix[i]
        if ch.isspace(): #Skip whitespace characters
            i += 1
            continue
        if ch in OPERATORS or ch in "()": #If the character is an operator or a parenthesis, add it as a token
            tokens.append(ch)
            i += 1
            continue
        if ch.isalpha() or ch == "_": #If the character starts a variable name, read the full variable name
            start = i
            i += 1
            while i < len(infix) and (infix[i].isalnum() or infix[i] == "_"): #Continue reading characters until we reach the end of the variable name
                i += 1
            tokens.append(infix[start:i])
            continue
        raise ValueError(f"Invalid character {ch!r} at position {i}.")
    return tokens


def Infix2Postfix(Infix: str) -> str:
    """Convert an infix logical expression to Reverse Polish notation."""
    output: List[str] = []
    stack: List[str] = []

    for token in tokenize(Infix): #Process each token in the infix expression
        if _is_variable(token): #If the token is a variable, add it to the output list
            output.append(token)
        elif token == "(":
            stack.append(token)
        elif token == ")":
            while stack and stack[-1] != "(": #Pop operators from the stack to the output list until we find a left parenthesis
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses: missing '('.")
            stack.pop()
        elif token in OPERATORS:
            while stack and stack[-1] in OPERATORS: #Pop operators from the stack to the output list while they have higher or equal precedence
                top = stack[-1]
                higher = PRECEDENCE[top] > PRECEDENCE[token] #Check if the operator on the stack has higher precedence than the current token
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

    while stack: #Pop any remaining operators from the stack to the output list
        top = stack.pop()
        if top in "()":
            raise ValueError("Mismatched parentheses.")
        output.append(top)

    return " ".join(output)


def _postfix_tokens(postfix: str | Sequence[str]) -> List[str]: #Helper function to split a postfix expression into tokens, similar to the tokenize function for infix expressions
    if isinstance(postfix, str):
        return postfix.split()
    return list(postfix)


def variables_from_postfix(postfix: str | Sequence[str]) -> Tuple[str, ...]: #Extracts the unique variable names from a postfix expression and returns them as a sorted tuple
    variables = sorted({token for token in _postfix_tokens(postfix) if _is_variable(token)}) #Use a set comprehension to collect unique variable names, then sort them and return as a tuple
    return tuple(variables)


def _apply_operator(operator: str, stack: List[bool]) -> None: #Apply a logical operator to the top elements of the stack. For unary operators like "~", pop one operand; for binary operators, pop two operands. Then push the result back onto the stack.
    if operator == "~": #For the NOT operator, we only need one operand. If the stack is empty, it means we don't have an operand to apply the operator to, so we raise an error. Otherwise, we pop the top value from the stack, apply the NOT operation, and push the result back onto the stack.
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
    """Generate a truth table from a postfix expression."""
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
    """Return the Disjunctive Normal Form represented by a truth table."""
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
    """Return True when two infix expressions have identical truth values."""
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

    # 2.4.1 Infix-to-Postfix conversion
    print("\n--- 2.4.1 Infix-to-Postfix Conversion ---")
    postfixes = []
    for index, infix in enumerate(TASK1_TESTCASES, start=1):
        postfix = Infix2Postfix(infix)
        postfixes.append(postfix)
        print(f"Testcase {index}: {infix}")
        print(f"Postfix  : {postfix}")
        print()

    # 2.4.2 Truth Tables
    print("\n--- 2.4.2 Truth Table - All 5 Testcases ---")
    tables = []
    for index, (infix, postfix) in enumerate(zip(TASK1_TESTCASES, postfixes), start=1):
        table = Postfix2Truthtable(postfix)
        tables.append(table)
        print(f"\nTestcase {index}: {infix}")
        print(format_truth_table(table))

    # 2.4.3 DNF Results
    print("\n--- 2.4.3 DNF Results ---")
    for index, (infix, table) in enumerate(zip(TASK1_TESTCASES, tables), start=1):
        print(f"Testcase {index}: {infix}")
        print(f"DNF: {GetDNF(table)}")
        print()

    # 2.4.4 Equivalence Check
    print("\n--- 2.4.4 Equivalence Check Results ---")
    for index, (left, right) in enumerate(EQUIVALENCE_TESTCASES, start=1):
        result = CheckEquivalence(left, right)
        print(f"Testcase {index}: {left}  <=>  {right}  =>  {result}")


if __name__ == "__main__":
    run_task1_demo()
