import pygame
import math
import random

# ---------------------------
# Pygame Initialization
# ---------------------------
pygame.init()
WIDTH, HEIGHT = 800, 600
# Creating a window for rendering graphics
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SketchScript 2.0 - a custom scripting language Interpreter by Harsh")
clock = pygame.time.Clock()

# ---------------------------
# Font Setup for UI Rendering
# ---------------------------
font = pygame.font.SysFont("monospace", 20)

# ---------------------------
# Global Interpreter State
# ---------------------------
# 'cursor' obj represents the drawing position, direction, and current drawing color.
cursor = {"x": WIDTH // 2, "y": HEIGHT // 2, "angle": 0, "color": (255, 255, 255)}
# 'symbols' stores variables and function definitions.
symbols = {}
# 'call_stack' is for saving/restoring state during function calls.
call_stack = []

# ---------------------------
# Color Definitions
# ---------------------------
COLORS = {
    "Red": (255, 0, 0),
    "Blue": (0, 0, 255),
    "Green": (0, 255, 0),
    "Black": (0, 0, 0)
}

# ---------------------------
# Reserved Keywords for the Language
# ---------------------------
# This set will be used to know when to stop parsing expressions.
COMMAND_KEYWORDS = {"SET", "DEFINE", "CALL", "IF", "WHILE", "MOVE", "TURN", "DRAW", "COLOR", "}", "{"}

# ---------------------------
# Syntax Help and Sample Program
# ---------------------------
SYNTAX = [
    "SketchScript 2.0 by Harsh Syntax:",
    "SET var = <expression>              - Assign a value to a variable",
    "DEFINE func ( param1 , param2 ) {  - Define a function",
    "  ...                               - Function body",
    "}                                   - End block",
    "CALL func ( arg1 , arg2 )          - Call a function",
    "IF <expr> <op> <expr> {            - If condition (op: >, <, =, !=)",
    "  ...                               - If body",
    "}",
    "WHILE <expr> <op> <expr> {         - While loop",
    "  ...                               - Loop body",
    "}",
    "MOVE <expr> Forward|Backward        - Move cursor",
    "TURN <expr> Right|Left              - Turn cursor",
    "DRAW Circle|Square|Star <expr>      - Draw shape with size",
    "DRAW ... AT <x> , <y>               - Draw at position",
    "COLOR Red|Blue|Green|Black|Random   - Set color",
    "Note: Use spaces around punctuation (e.g., = , { })"
]

# A sample SketchScript program
SAMPLE_CODE = """
SET speed = 30
DEFINE spiral ( n ) {
  IF n > 0 {
    MOVE speed * n Forward
    TURN 60 Right
    CALL spiral ( n - 1 )
  }
}
COLOR Random
SET layers = 3
WHILE layers > 0 {
  CALL spiral ( 5 )
  MOVE 20 Backward
  SET layers = layers - 1
}
DRAW Star 15 AT 400 , 300
"""


# ---------------------------
# Tokenizer: Convert code string into tokens
# ---------------------------
def tokenize(code):
    # Insert spaces around block symbols and punctuation so they become separate tokens.
    for ch in ["{", "}", "(", ")", ","]:
        code = code.replace(ch, f" {ch} ")
    # Ensure that operators are separated by spaces.
    for op in ["+", "-", "*", "/", "=", ">", "<", "!"]:
        code = code.replace(op, f" {op} ")
    # Split code into tokens and filter out any empty strings.
    tokens = [tok for tok in code.split() if tok]

    # Combine tokens to handle multi-character operators like "!="
    i = 0
    combined = []
    while i < len(tokens):
        if tokens[i] == "!" and i + 1 < len(tokens) and tokens[i + 1] == "=":
            combined.append("!=")
            i += 2
        else:
            combined.append(tokens[i])
            i += 1
    return combined


# ---------------------------
# Expression Parser: Recursive-Descent Parsing
# ---------------------------
def parse_expression(tokens, i, stop_tokens=None):
    # Default to an empty set if no stop tokens are provided.
    if stop_tokens is None:
        stop_tokens = set()
    # Parse a term first (handles multiplication/division)
    node, i = parse_term(tokens, i, stop_tokens)
    # Process addition and subtraction in a left-associative manner.
    while i < len(tokens) and tokens[i] in ("+", "-") and tokens[i] not in stop_tokens:
        op = tokens[i]
        i += 1
        right, i = parse_term(tokens, i, stop_tokens)
        node = {"op": op, "left": node, "right": right}
    return node, i


def parse_term(tokens, i, stop_tokens):
    # Parse a factor (handles basic numbers, variables, and parenthesized expressions)
    node, i = parse_factor(tokens, i, stop_tokens)
    # Process multiplication and division operators.
    while i < len(tokens) and tokens[i] in ("*", "/") and tokens[i] not in stop_tokens:
        op = tokens[i]
        i += 1
        right, i = parse_factor(tokens, i, stop_tokens)
        node = {"op": op, "left": node, "right": right}
    return node, i


def parse_factor(tokens, i, stop_tokens):
    # Check for unexpected end-of-tokens.
    if i >= len(tokens):
        raise Exception("Unexpected end of tokens in expression")
    token = tokens[i]
    if token in stop_tokens:
        raise Exception(f"Unexpected token '{token}' in expression")
    # Handle parenthesized expressions.
    if token == "(":
        node, i = parse_expression(tokens, i + 1, stop_tokens.union({")"}))
        if i >= len(tokens) or tokens[i] != ")":
            raise Exception("Expected )")
        return node, i + 1
    # Handle numbers (both integers and decimals).
    elif token.replace('.', '', 1).isdigit():
        return float(token), i + 1
    # Treat remaining tokens as variables (even if they match a reserved keyword)
    elif token.isalpha() or token in COMMAND_KEYWORDS:
        return token, i + 1
    else:
        raise Exception("Unexpected token in expression: " + token)


def parse_full_expression(token_list):
    # Parse a complete expression from a list of tokens.
    expr, i = parse_expression(token_list, 0)
    if i != len(token_list):
        raise Exception("Extra tokens in expression: " + " ".join(token_list[i:]))
    return expr


def parse_expression_until(tokens, start, stop_tokens):
    # Collect tokens until one of the stop tokens is encountered.
    end = start
    while end < len(tokens) and tokens[end] not in stop_tokens:
        end += 1
    expr = parse_full_expression(tokens[start:end])
    return expr, end


# ---------------------------
# Expression Evaluators
# ---------------------------
def eval_expr(expr):
    # Evaluate an arithmetic expression recursively.
    if isinstance(expr, dict):
        left = eval_expr(expr["left"])
        right = eval_expr(expr["right"])
        op = expr["op"]
        if op == "+": return left + right
        if op == "-": return left - right
        if op == "*": return left * right
        if op == "/": return left / right if right != 0 else 0
    elif isinstance(expr, (int, float)):
        return expr
    elif isinstance(expr, str):
        # Return the variable's value from the symbols dictionary; default to 0 if undefined.
        return symbols.get(expr, 0)
    else:
        raise Exception("Cannot evaluate expression: " + str(expr))


def eval_condition(cond):
    # Evaluate a condition by comparing two evaluated expressions.
    left = eval_expr(cond["left"])
    right = eval_expr(cond["right"])
    op = cond["op"]
    if op == ">": return left > right
    if op == "<": return left < right
    if op == "=": return left == right
    if op == "!=": return left != right
    return False


# ---------------------------
# Condition Parser: Parses binary conditions
# ---------------------------
def parse_condition(tokens, i):
    # Parse the left-hand side expression for the condition.
    left, i = parse_expression(tokens, i, stop_tokens={">", "<", "=", "!="})
    if i >= len(tokens):
        raise Exception("Expected operator in condition")
    op = tokens[i]
    if op not in (">", "<", "=", "!="):
        raise Exception("Expected comparison operator, got " + op)
    i += 1
    # Parse the right-hand side expression.
    right, i = parse_expression(tokens, i, stop_tokens={"{"})
    return {"left": left, "op": op, "right": right}, i


# ---------------------------
# Block End Finder: Matches opening and closing braces
# ---------------------------
def find_block_end(tokens, start):
    depth = 1  # Starting with one open brace
    i = start
    while i < len(tokens) and depth > 0:
        if tokens[i] == "{":
            depth += 1
        elif tokens[i] == "}":
            depth -= 1
        i += 1
    return i


# ---------------------------
# Drawing Functions
# ---------------------------
def move_cursor(distance, direction):
    # Save the current cursor position.
    old_x, old_y = cursor["x"], cursor["y"]
    angle_rad = math.radians(cursor["angle"])
    # Update the cursor's position based on its current angle.
    if direction == "Forward":
        cursor["x"] += distance * math.cos(angle_rad)
        cursor["y"] += distance * math.sin(angle_rad)
    elif direction == "Backward":
        cursor["x"] -= distance * math.cos(angle_rad)
        cursor["y"] -= distance * math.sin(angle_rad)
    # Draw a line from the old position to the new position.
    pygame.draw.line(screen, cursor["color"], (old_x, old_y), (cursor["x"], cursor["y"]), 2)


def draw_shape(shape, size, x=None, y=None):
    # Determine the position to draw the shape. Use provided coordinates if available.
    pos = (int(x) if x is not None else int(cursor["x"]),
           int(y) if y is not None else int(cursor["y"]))
    if shape == "Circle":
        pygame.draw.circle(screen, cursor["color"], pos, int(size), 2)
    elif shape == "Square":
        pygame.draw.rect(screen, cursor["color"],
                         (pos[0] - int(size) // 2, pos[1] - int(size) // 2, int(size), int(size)), 2)
    elif shape == "Star":
        # Calculate star points for a 5-point star
        points = []
        for i in range(5):
            angle = i * 4 * math.pi / 5
            points.append((pos[0] + size * math.cos(angle), pos[1] + size * math.sin(angle)))
            angle += 2 * math.pi / 5
            points.append((pos[0] + size * 0.5 * math.cos(angle), pos[1] + size * 0.5 * math.sin(angle)))
        pygame.draw.polygon(screen, cursor["color"], points, 2)


# ---------------------------
# Interpreter: Process Tokens and Execute Commands
# ---------------------------
def interpret(tokens):
    global cursor, symbols, call_stack
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # Variable assignment: SET var = <expression>
        if token == "SET":
            var = tokens[i + 1]
            if tokens[i + 2] != "=":
                raise Exception("Expected '=' in SET statement")
            expr, new_i = parse_expression(tokens, i + 3, stop_tokens=COMMAND_KEYWORDS)
            symbols[var] = eval_expr(expr)
            i = new_i

        # Function definition: DEFINE func ( param1 , param2 ) { ... }
        elif token == "DEFINE":
            func_name = tokens[i + 1]
            if tokens[i + 2] != "(":
                raise Exception("Expected ( after function name in DEFINE")
            j = i + 3
            params = []
            while tokens[j] != ")":
                if tokens[j] != ",":
                    params.append(tokens[j])
                j += 1
            if tokens[j + 1] != "{":
                raise Exception("Expected { to start function body")
            body_start = j + 2
            body_end = find_block_end(tokens, body_start)
            func_body = tokens[body_start:body_end - 1]  # Exclude closing brace
            symbols[func_name] = {"params": params, "body": func_body}
            i = body_end

        # Function call: CALL func ( arg1 , arg2 )
        elif token == "CALL":
            func_name = tokens[i + 1]
            if tokens[i + 2] != "(":
                raise Exception("Expected ( in function call")
            j = i + 3
            args = []
            arg_tokens = []
            while tokens[j] != ")":
                if tokens[j] == ",":
                    if arg_tokens:
                        args.append(parse_full_expression(arg_tokens))
                        arg_tokens = []
                else:
                    arg_tokens.append(tokens[j])
                j += 1
            if arg_tokens:
                args.append(parse_full_expression(arg_tokens))
            func = symbols.get(func_name)
            if func is None:
                raise Exception("Undefined function: " + func_name)
            if len(args) != len(func["params"]):
                raise Exception("Function " + func_name + " expects " + str(len(func["params"])) +
                                " arguments, got " + str(len(args)))
            # Set up the local scope for the function call
            local_scope = {}
            for param, arg_expr in zip(func["params"], args):
                local_scope[param] = eval_expr(arg_expr)
            call_stack.append(symbols.copy())
            symbols.update(local_scope)
            interpret(func["body"])
            # Restore previous state after function execution
            symbols.clear()
            symbols.update(call_stack.pop())
            i = j + 1

        # Conditional execution: IF <condition> { ... }
        elif token == "IF":
            cond, new_i = parse_condition(tokens, i + 1)
            if tokens[new_i] != "{":
                raise Exception("Expected { after IF condition")
            block_start = new_i + 1
            block_end = find_block_end(tokens, block_start)
            if eval_condition(cond):
                interpret(tokens[block_start:block_end - 1])
            i = block_end

        # Loop execution: WHILE <condition> { ... }
        elif token == "WHILE":
            cond, new_i = parse_condition(tokens, i + 1)
            if tokens[new_i] != "{":
                raise Exception("Expected { after WHILE condition")
            block_start = new_i + 1
            block_end = find_block_end(tokens, block_start)
            while eval_condition(cond):
                interpret(tokens[block_start:block_end - 1])
            i = block_end

        # Cursor movement: MOVE <expression> Forward|Backward
        elif token == "MOVE":
            expr, new_i = parse_expression(tokens, i + 1, stop_tokens={"Forward", "Backward"})
            distance = eval_expr(expr)
            direction = tokens[new_i]
            move_cursor(distance, direction)
            i = new_i + 1

        # Cursor rotation: TURN <expression> Right|Left
        elif token == "TURN":
            expr, new_i = parse_expression(tokens, i + 1, stop_tokens={"Right", "Left"})
            angle_val = eval_expr(expr)
            direction = tokens[new_i]
            if direction == "Right":
                cursor["angle"] += angle_val
            elif direction == "Left":
                cursor["angle"] -= angle_val
            i = new_i + 1

        # Drawing a shape: DRAW <shape> <expression> [AT <x> , <y>]
        elif token == "DRAW":
            shape = tokens[i + 1]
            expr, new_i = parse_expression(tokens, i + 2,
                                           stop_tokens={"AT", "SET", "DEFINE", "CALL", "IF", "WHILE", "MOVE", "TURN",
                                                        "DRAW", "COLOR", "}"})
            size = eval_expr(expr)
            i = new_i
            x_val = None
            y_val = None
            # Optional position specifier for drawing the shape
            if i < len(tokens) and tokens[i] == "AT":
                i += 1
                x_expr, i = parse_expression(tokens, i, stop_tokens={","})
                x_val = eval_expr(x_expr)
                if tokens[i] == ",":
                    i += 1
                y_expr, i = parse_expression(tokens, i, stop_tokens=COMMAND_KEYWORDS)
                y_val = eval_expr(y_expr)
            draw_shape(shape, size, x_val, y_val)

        # Color setting: COLOR <color>
        elif token == "COLOR":
            color = tokens[i + 1]
            if color == "Random":
                cursor["color"] = random.choice(list(COLORS.values()))
            else:
                cursor["color"] = COLORS.get(color, (255, 255, 255))
            i += 2

        # If token doesn't match any known command, move to next token.
        else:
            i += 1


# ---------------------------
# UI State Management for Editor/Runner Modes
# ---------------------------
STATE_SYNTAX = "syntax"  # Show syntax help/instructions
STATE_INPUT = "input"  # Accept user input for SketchScript code
STATE_RUNNING = "running"  # Display the interpreter's drawing output
current_state = STATE_SYNTAX

# ---------------------------
# Input Handling Variables
# ---------------------------
user_input = ""
cursor_blink = 0
use_sample = False  # If True, use the SAMPLE_CODE as input

# ---------------------------
# Main Application Loop
# ---------------------------
running_main = True
while running_main:
    for event in pygame.event.get():
        # Handle quit events
        if event.type == pygame.QUIT:
            running_main = False

        # Process keyboard input for each state
        elif event.type == pygame.KEYDOWN:
            if current_state == STATE_INPUT:
                # When the user presses Enter, run the code
                if event.key == pygame.K_RETURN:
                    current_state = STATE_RUNNING
                    code = SAMPLE_CODE if use_sample else user_input
                    # Clear the screen and run the interpreter once
                    screen.fill((20, 20, 20))
                    tokens = tokenize(code)
                    interpret(tokens)
                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]
                elif event.key == pygame.K_TAB:
                    # TAB key loads the sample program
                    use_sample = True
                    user_input = SAMPLE_CODE
                elif event.unicode.isprintable():
                    user_input += event.unicode
            elif current_state == STATE_SYNTAX and event.key == pygame.K_SPACE:
                # Press SPACE to switch from syntax help to code input
                current_state = STATE_INPUT
            elif current_state == STATE_RUNNING and event.key == pygame.K_r:
                # Press 'R' to restart the program (go back to syntax help)
                current_state = STATE_SYNTAX
                user_input = ""
                use_sample = False
                cursor = {"x": WIDTH // 2, "y": HEIGHT // 2, "angle": 0, "color": (255, 255, 255)}
                symbols.clear()
                call_stack.clear()

    # ---------------------------
    # UI Rendering Based on Current State
    # ---------------------------
    if current_state == STATE_SYNTAX:
        # Clear screen and display syntax instructions.
        screen.fill((20, 20, 20))
        for i, line in enumerate(SYNTAX):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (10, 10 + i * 25))
        instr = font.render("Press SPACE to start writing", True, (255, 255, 0))
        screen.blit(instr, (10, HEIGHT - 40))
    elif current_state == STATE_INPUT:
        # Clear screen and display the code editor prompt.
        screen.fill((20, 20, 20))
        prompt = font.render("Type your program (TAB for sample, ENTER to run):", True, (255, 255, 0))
        screen.blit(prompt, (10, 10))
        # Render each line of user input.
        lines = user_input.split("\n")
        y_offset = 40
        for line in lines:
            words = line.split()
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                if font.size(test_line)[0] < WIDTH - 20:
                    current_line = test_line
                else:
                    text = font.render(current_line, True, (255, 255, 255))
                    screen.blit(text, (10, y_offset))
                    y_offset += 25
                    current_line = word + " "
            if current_line:
                text = font.render(current_line, True, (255, 255, 255))
                screen.blit(text, (10, y_offset))
                y_offset += 25

        # Render a blinking cursor in the code editor.
        cursor_blink = (cursor_blink + 1) % 30
        if cursor_blink < 15:
            cursor_pos = font.size(user_input)[0] + 15
            pygame.draw.line(screen, (255, 255, 255), (cursor_pos, y_offset - 20), (cursor_pos, y_offset), 2)
    elif current_state == STATE_RUNNING:
        # Do not clear the screen in running state so that drawings persist.
        instr = font.render("Press R to restart", True, (255, 255, 0))
        screen.blit(instr, (10, HEIGHT - 40))

    # Update the display and cap the frame rate.
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
