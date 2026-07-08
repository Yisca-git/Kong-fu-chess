#https://github.com/Yisca-git/Kong-fu-chess  - My GitHub repository for this project

import sys
import board_parser
from game import KungFuChess

def main():
    # Read raw input from standard input
    input_text = sys.stdin.read().strip()
    if not input_text:
        return

    # Pass the raw input to the parser module for syntax and structural validation
    raw_rows = board_parser.parse_and_validate_board(input_text)
    
    # Terminate if the validation fails (errors are already printed inside the parser)
    if raw_rows is None:
        return

    # Initialize the dynamic game instance with the validated board
    game = KungFuChess(raw_rows)

    # Extract command lines following the "Commands:" header
    lines = [line.strip() for line in input_text.splitlines() if line.strip()]
    commands_start = lines.index("Commands:") + 1
    command_lines = lines[commands_start:]

    # Parse and execute commands sequentially
    for cmd in command_lines:
        if cmd.startswith("click"):
            parts = cmd.split()
            if len(parts) == 3:
                game.handle_click(int(parts[1]), int(parts[2]))
                
        elif cmd.startswith("jump"):
            parts = cmd.split()
            if len(parts) == 3:
                game.handle_jump(int(parts[1]), int(parts[2]))
                
        elif cmd.startswith("wait"):
            parts = cmd.split()
            if len(parts) == 2:
                game.handle_wait(int(parts[1]))
                
        elif cmd == "print board":
            game.print_board()

if __name__ == "__main__":
    main()