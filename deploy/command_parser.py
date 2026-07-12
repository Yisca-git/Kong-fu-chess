def parse_commands(text: str) -> list[tuple]:
    """Parses the Commands section of the input into a list of command tuples."""
    lines = [l.rstrip() for l in text.splitlines()]
    commands_start = lines.index("Commands:") + 1
    commands = []
    i = commands_start

    def is_cmd(l):
        s = l.strip()
        return s.startswith("click") or s.startswith("wait") or s.startswith("jump") or s == "print board"

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("click"):
            parts = line.split()
            commands.append(("click", int(parts[1]), int(parts[2])))
            i += 1
        elif line.startswith("jump"):
            parts = line.split()
            commands.append(("jump", int(parts[1]), int(parts[2])))
            i += 1
        elif line.startswith("wait"):
            commands.append(("wait", int(line.split()[1])))
            i += 1
        elif line == "print board":
            i += 1
            while i < len(lines) and lines[i].strip() and not is_cmd(lines[i]):
                i += 1
            commands.append(("print",))
        else:
            i += 1

    return commands
