import tkinter as tk
from tkinter import messagebox

# denotes type and value of token 
class Token: 
    def __init__(self, type_, value):
        self.type = type_
        self.value = value
    def __repr__(self):
        return f"Token({self.type}, {self.value})"
    
# order of operator precedence, higher number means higher priority
OPERATORS = { 
    '+': 1, '-': 1, '*': 2, '/': 2,
    '==': 0, '!=': 0, '<': 0, '>': 0, '<=': 0, '>=': 0,
    'and': -1, 'or': -2, '!': 3, '_NEG': 4
}

# all operators are read from left excluding exceptions to ensure correct expression results
LEFT_ASSOC = {op: True for op in OPERATORS}
LEFT_ASSOC['!'] = False
LEFT_ASSOC['_NEG'] = False

globals_env = {} # global environment for the interpreter independent of python built in variables 

# all numbers are treated as floats for simplicity and uniform type
def is_number(s):
    try:
        float(s)
        return True
    except:
        return False

# checks if inputted strings are valid and do not contain any reserved keywords or inappropriate symbols
def is_identifier(s): 
    return s and (s[0].isalpha() or s[0] == '_') and all(c.isalnum() or c == '_' for c in s)

# breaks input into tokens by detecting boolean / floats / strings
def tokenize(expr):
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isspace():
            i += 1
            continue
        elif expr[i].isdigit() or (expr[i] == '.' and i + 1 < len(expr) and expr[i + 1].isdigit()):
            num = ''
            dot_count = 0
            while i < len(expr) and (expr[i].isdigit() or expr[i] == '.'):
                if expr[i] == '.':
                    dot_count += 1
                    if dot_count > 1:
                        break
                num += expr[i]
                i += 1
            tokens.append(num)
        elif expr[i].isalpha() or expr[i] == '_':
            id_str = ''
            while i < len(expr) and (expr[i].isalnum() or expr[i] == '_'):
                id_str += expr[i]
                i += 1
            tokens.append(id_str)
        elif expr[i] in ('=', '!', '<', '>'):
            if i + 1 < len(expr) and expr[i + 1] == '=':
                tokens.append(expr[i] + '=')
                i += 2
            else:
                tokens.append(expr[i])
                i += 1
        elif expr[i] in ('+', '-', '*', '/', '(', ')'):
            tokens.append(expr[i])
            i += 1
        elif expr[i] == '"':
            i += 1
            str_lit = ''
            while i < len(expr) and expr[i] != '"':
                str_lit += expr[i]
                i += 1
            i += 1
            tokens.append('"' + str_lit + '"')
        else:
            raise ValueError(f"Unexpected character: {expr[i]}")
    return tokens

# converts raw strings to tokens and converts strings true and false to True and False
def lex(expr):
    raw_tokens = tokenize(expr)
    tokens = []
    prev_token = None

    for word in raw_tokens:
        lw = word.lower()
        if word.startswith('"') and word.endswith('"'):
            tokens.append(Token('STRING', word[1:-1]))
        elif lw == 'print':
            tokens.append(Token('PRINT', word))
        elif word == '=':
            tokens.append(Token('ASSIGN', word))
        elif lw == 'true':
            tokens.append(Token('BOOLEAN', True))
        elif lw == 'false':
            tokens.append(Token('BOOLEAN', False))
        elif word in OPERATORS:
            if word == '-' and (prev_token is None or prev_token.type in ('OPERATOR', 'LPAREN', 'ASSIGN')):
                tokens.append(Token('OPERATOR', '_NEG'))
            else:
                tokens.append(Token('OPERATOR', word))
        elif word == '(':
            tokens.append(Token('LPAREN', word))
        elif word == ')':
            tokens.append(Token('RPAREN', word))
        elif is_number(word):
            tokens.append(Token('NUMBER', float(word)))
        elif is_identifier(word):
            tokens.append(Token('IDENTIFIER', word))
        else:
            raise ValueError(f"Unknown token: {word}")
        prev_token = tokens[-1]
    return tokens

# converts infix to postfix to make expression evaluations easier
def to_postfix(tokens):
    output = []
    stack = []
    for token in tokens:
        if token.type in ('NUMBER', 'STRING', 'BOOLEAN', 'IDENTIFIER'):
            output.append(token)
        elif token.type == 'OPERATOR':
            while stack and stack[-1].type == 'OPERATOR':
                top = stack[-1]
                if (LEFT_ASSOC[token.value] and OPERATORS[token.value] <= OPERATORS[top.value]) or \
                   (not LEFT_ASSOC[token.value] and OPERATORS[token.value] < OPERATORS[top.value]):
                    output.append(stack.pop())
                else:
                    break
            stack.append(token)
        elif token.type == 'LPAREN':
            stack.append(token)
        elif token.type == 'RPAREN':
            while stack and stack[-1].type != 'LPAREN':
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses")
            stack.pop()
    while stack:
        if stack[-1].type in ('LPAREN', 'RPAREN'):
            raise ValueError("Mismatched parentheses")
        output.append(stack.pop())
    return output

# evaluates expressions using a stack
def evaluate_postfix(postfix):
    stack = []
    for token in postfix:
        if token.type in ('NUMBER', 'STRING', 'BOOLEAN'):
            stack.append(token.value)
        elif token.type == 'IDENTIFIER':
            if token.value not in globals_env:
                raise ValueError(f"Variable '{token.value}' is not defined")
            stack.append(globals_env[token.value])
        elif token.type == 'OPERATOR':
            if token.value == '!':
                val = stack.pop()
                if not isinstance(val, bool):
                    raise ValueError("'!' expects a boolean")
                stack.append(not val)
            elif token.value == '_NEG':
                val = stack.pop()
                if not isinstance(val, (int, float)):
                    raise ValueError("Unary minus expects a number")
                stack.append(-val)
            else:
                b = stack.pop()
                a = stack.pop()
                if token.value == '+':
                    stack.append(str(a) + str(b) if isinstance(a, str) or isinstance(b, str) else a + b)
                elif token.value == '-':
                    stack.append(a - b)
                elif token.value == '*':
                    if isinstance(a, str) and isinstance(b, (int, float)):
                        stack.append(a * int(b))
                    elif isinstance(b, str) and isinstance(a, (int, float)):
                        stack.append(b * int(a))
                    else:
                        stack.append(a * b)
                elif token.value == '/':
                    stack.append(a / b)
                elif token.value == '==':
                    stack.append(a == b)
                elif token.value == '!=':
                    stack.append(a != b)
                elif token.value == '<':
                    stack.append(a < b)
                elif token.value == '>':
                    stack.append(a > b)
                elif token.value == '<=':
                    stack.append(a <= b)
                elif token.value == '>=':
                    stack.append(a >= b)
                elif token.value == 'and':
                    if isinstance(a, bool) and isinstance(b, bool):
                        stack.append(a and b)
                    else:
                        raise ValueError("'and' expects booleans")
                elif token.value == 'or':
                    if isinstance(a, bool) and isinstance(b, bool):
                        stack.append(a or b)
                    else:
                        raise ValueError("'or' expects booleans")
                else:
                    raise ValueError(f"Unknown operator {token.value}")
    if len(stack) != 1:
        raise ValueError("Invalid expression")
    return stack[0]

# tokenises and parses the input, ready to be presented back to the user
def execute_line(line):
    tokens = lex(line)
    if not tokens:
        return None
    if tokens[0].type == 'PRINT':
        expr = tokens[1:]
        result = evaluate_postfix(to_postfix(expr))
        return result
    if len(tokens) >= 3 and tokens[1].type == 'ASSIGN' and tokens[0].type == 'IDENTIFIER':
        var_name = tokens[0].value
        expr = tokens[2:]
        value = evaluate_postfix(to_postfix(expr))
        globals_env[var_name] = value
        return f"{var_name} = {value}"
    result = evaluate_postfix(to_postfix(tokens))
    return result

# gathers input from the gui, then shows expression result or error
def evaluate_expression():
    expr = input_field.get()
    try:
        result = execute_line(expr)
        result_label.config(text=f"Result: {result}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# user interface for user input
root = tk.Tk()
root.title("Interpreter GUI")

tk.Label(root, text="Enter an expression:").pack(pady=5)
input_field = tk.Entry(root, width=60)
input_field.pack(padx=10)
tk.Button(root, text="Evaluate", command=evaluate_expression).pack(pady=5)
result_label = tk.Label(root, text="Result: ")
result_label.pack(pady=10)
root.mainloop()
