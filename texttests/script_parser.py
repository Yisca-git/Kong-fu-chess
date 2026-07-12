from dataclasses import dataclass


@dataclass(frozen=True)
class ClickCommand:
    x: int
    y: int


@dataclass(frozen=True)
class WaitCommand:
    ms: int


@dataclass(frozen=True)
class PrintBoardCommand:
    expected: tuple[str, ...]


Command = ClickCommand | WaitCommand | PrintBoardCommand


def parse_script(text: str) -> tuple[str, list[Command]]:
    """Parses a DSL script into a board text and a list of commands.
    Returns the raw board section and the parsed command list."""
    lines = [l.rstrip() for l in text.splitlines()]

    board_start = lines.index("Board:") + 1
    commands_start = lines.index("Commands:")
    board_text = "\n".join(["Board:"] + lines[board_start:commands_start] + ["Commands:"])

    commands: list[Command] = []
    i = commands_start + 1

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        if line.startswith("click"):
            parts = line.split()
            commands.append(ClickCommand(int(parts[1]), int(parts[2])))
            i += 1

        elif line.startswith("wait"):
            parts = line.split()
            commands.append(WaitCommand(int(parts[1])))
            i += 1

        elif line == "print board":
            i += 1
            expected = []
            while i < len(lines) and lines[i].strip() and not _is_command(lines[i].strip()):
                expected.append(lines[i].strip())
                i += 1
            commands.append(PrintBoardCommand(tuple(expected)))

        else:
            i += 1

    return board_text, commands


def _is_command(line: str) -> bool:
    return line.startswith("click") or line.startswith("wait") or line == "print board"
