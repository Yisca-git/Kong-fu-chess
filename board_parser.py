from config import VALID_PIECES, VALID_COLORS, EMPTY

def parse_and_validate_board(input_text):
    if not input_text:
        return None

    # Clean and split input into lines, ignoring empty lines
    lines = [line.strip() for line in input_text.splitlines() if line.strip()]
    
    try:
        # Dynamically slice the board section between headers
        board_start = lines.index("Board:") + 1
        board_end = lines.index("Commands:")
        raw_rows = lines[board_start:board_end]
    except ValueError:
        return None

    expected_width = len(raw_rows[0].split()) if raw_rows else 0

    for row in raw_rows:
        pieces_in_row = row.split()
        if len(pieces_in_row) != expected_width:
            print("ERROR ROW_WIDTH_MISMATCH")
            return None
        for piece in pieces_in_row:
            if piece != EMPTY and (len(piece) != 2 or piece[0] not in VALID_COLORS or piece[1] not in VALID_PIECES):
                print("ERROR UNKNOWN_TOKEN")
                return None

    return raw_rows