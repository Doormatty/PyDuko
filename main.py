import random
from typing import Iterator, Optional

from rich.console import Console
from rich.text import Text

console = Console()


class Board:
    class BoardException(Exception):
        """Custom exception class for Board-related errors."""

    def __init__(self, state: Optional[str] = None):
        """
        Initialize the Board with an optional state.

        :param state: A string representation of the board's state. Defaults to None.
        """
        self.board: dict[tuple[int, int], 'Cell'] = {}

        for y in range(9):
            for x in range(9):
                self.board[(x, y)] = Cell(x=x, y=y, value=None, board=self)

        if state is not None:
            self.load_from_string(state)

    def __hash__(self) -> int:
        """
        Compute a unique hash value for the current state of the board.

        :return: An integer hash value.
        """
        return hash(tuple(self.board.items()))

    def __eq__(self, other: 'Board') -> bool:
        if not isinstance(other, Board):
            raise NotImplementedError
        for cell in self.iter_cells():
            if cell != other.board[(cell.x, cell.y)]:
                return False
        return True

    def clone(self) -> 'Board':
        """
        Create a clone of the given board.

        :param board: A Board instance to be cloned.
        :return: A new Board instance which is a clone of the given board.
        """
        new_board = Board()
        new_board.board = {k: v.clone(new_board) for k, v in self.board.items()}
        return new_board

    def copy_from(self, board: 'Board') -> None:
        """
        Copy the state from another board to this board.

        :param board: A Board instance to copy from.
        """
        self.board = {k: v.clone(self) for k, v in board.board.items()}

    def set_cell(self, x: int, y: int, value: int) -> None:
        """
        Set the value of a specific cell on the board.

        :param x: The x-coordinate of the cell.
        :param y: The y-coordinate of the cell.
        :param value: The value to be set in the cell.
        """
        self.board[(x, y)].value = value

    def iter_cells(self) -> Iterator['Cell']:
        """
        Iterate over all cells in the board.

        :return: An iterator of Cell objects.
        """
        for y in range(9):
            for x in range(9):
                yield self.board[(x, y)]

    def clear_board(self) -> None:
        """
        Clear the board by resetting all cells to their default state.
        """
        for cell in self.iter_cells():
            cell.possibles.clear()
            cell.value = None

    def is_solved(self) -> bool:
        """
        Check if the board is completely solved.

        :return: True if the board is solved, False otherwise.
        """
        if not self.is_valid():
            raise self.BoardException("The board is not valid.")
        return all(cell.value is not None for cell in self.board.values())

    def would_be_valid(self, x, y, value) -> bool:
        clone = self.clone()
        clone.set_cell(x=x, y=y, value=value)
        return clone.is_valid()

    def solve(self) -> None:
        """
        Attempt to solve the board. Raises BoardException if the board is unsolvable.
        """
        iterations = 1
        while True:
            for cell in self.iter_cells():
                if cell.value is None:
                    cell.get_possible_values()
                    if len(cell.possibles) == 0:
                        raise self.BoardException(f"Cell({cell.x}, {cell.y}) has no possible values!")

                    if len(cell.possibles) == 1:
                        cell.value = cell.possibles.pop()
                        # print(f"Cell({cell.x}, {cell.y}) is solved - {cell.value}")
                if not self.is_valid():
                    raise self.BoardException(f"Board is not valid!")

            # Check how many unsolved cells still exist
            unsolved_count = self.get_unsolved_count()
            if unsolved_count == 0:
                print(f"Solved in {iterations} iterations")
                self.print_board()
                return
            iterations += 1

    def solve_sudoku(self):
        for cell in self.iter_cells():
            if cell.value is None:
                nums = [1, 2, 3, 4, 5, 6, 7, 8, 9]
                random.shuffle(nums)
                for num in nums:
                    if self.would_be_valid(cell.x, cell.y, num):
                        self.board[(cell.x, cell.y)].value = num

                        if self.solve_sudoku():
                            return True

                        # Backtrack
                        self.board[(cell.x, cell.y)].value = None
                return False
        return True

    def is_valid(self) -> bool:
        """
        Check if the current board state is valid.

        :return: True if valid, False otherwise.
        """
        for i in range(9):
            row = self.get_row(i)
            if len(set(row)) != len(row):
                return False

            col = self.get_column(i)
            if len(set(col)) != len(col):
                return False

            chunk = self.get_chunk(i)
            if len(set(chunk)) != len(chunk):
                return False
        return True

    def update_all_cells_possible_values(self) -> None:
        """
        Update possible values for all cells based on current board state.
        """
        for cell in self.iter_cells():
            if cell.value is None:
                cell.get_possible_values()

    def count_all_possible_values(self) -> int:
        """
        Count the total number of possible values for all unsolved cells.

        :return: Total number of possible values.
        """
        count = 0
        for cell in self.board.values():
            count += len(cell.possibles)
        return count

    def load_from_string(self, board_string: str) -> None:
        """
        Load a board state from a string.

        :param board_string: A string representation of the board state.
        :raises BoardException: If the string is not 81 characters long.
        """
        if len(board_string) != 81:
            raise self.BoardException("Invalid board string length")
        self.clear_board()
        for i, value in enumerate(board_string):
            x = i % 9
            y = i // 9
            if value.isdigit():
                self.board[(x, y)].value = int(value)
            else:
                self.board[(x, y)].value = None

    def save_to_string(self) -> str:
        """
        Save the current board state to a string.

        :return: A string representation of the board state.
        """
        retval = ""
        for cell in self.board.values():
            retval += str(cell.value) if cell.value is not None else "."
        return retval

    # ========== Get Commands ==========

    def get_column(self, x: int) -> list[int]:
        """
        Get all values in a specific column.

        :param x: The x-coordinate (column index).
        :return: A list of values in the specified column.
        """
        return [self.board[(x, y)].value for y in range(9) if self.board[(x, y)].value is not None]

    def get_row(self, y: int) -> list[int]:
        """
        Get all values in a specific row.

        :param y: The y-coordinate (row index).
        :return: A list of values in the specified row.
        """
        return [self.board[(x, y)].value for x in range(9) if self.board[(x, y)].value is not None]

    def get_chunk(self, i: int) -> list[int]:
        """
        Get all values in a specific 3x3 chunk of the board.

        :param i: Index of the chunk.
        :return: A list of values in the specified chunk.
        """
        chunk = []
        x_start = (i % 3) * 3
        y_start = (i // 3) * 3
        for y in range(y_start, y_start + 3):
            for x in range(x_start, x_start + 3):
                t_cell = self.board[(x, y)]
                if t_cell.value is not None:
                    chunk.append(t_cell.value)
        return chunk

    def get_cell_str(self, x: int, y: int, blank: int | str = " ") -> str:
        """
        Get a string representation of the value of a specific cell, or a blank placeholder if the cell is unsolved.

        :param x: The x-coordinate of the cell.
        :param y: The y-coordinate of the cell.
        :param blank: A placeholder value for unsolved cells. Defaults to " ".
        :return: The value of the cell or the blank placeholder.
        """
        retval = self.board[(x, y)].value
        if retval is None:
            return blank
        else:
            return str(retval)

    def get_cell(self, x: int, y: int) -> int | None:
        """
        Get the value of a specific cell, or a blank placeholder if the cell is unsolved.

        :param x: The x-coordinate of the cell.
        :param y: The y-coordinate of the cell.
        :return: The value of the cell or None.
        """
        return self.board[(x, y)].value

    def get_unsolved_cells(self) -> list['Cell']:
        """
        Get a list of all unsolved cells.

        :return: A list of Cell objects that are unsolved.
        """
        return [cell for cell in self.board.values() if cell.value is None]

    def get_solved_cells(self) -> list['Cell']:
        """
        Get a list of all solved cells.

        :return: A list of Cell objects that are solved.
        """
        return [cell for cell in self.board.values() if cell.value is not None]

    def clear_random_cell(self):
        random_cell = random.choice(self.get_solved_cells())
        random_cell.clear()

    def get_unsolved_count(self) -> int:
        """
        Count the number of unsolved cells.

        :return: The number of unsolved cells.
        """
        return len(self.get_unsolved_cells())

    # ========== Print Commands ==========
    def print_board_line(self, y, compact=False, green=None, red=None):
        if green is None:
            green = ()
        if red is None:
            red = ()
        # Print the header
        if y == 0:
            if compact:
                print("╔═══╦═══╦═══╗")
            else:
                print("╔═╤═╤═╦═╤═╤═╦═╤═╤═╗")
        retval = Text("║")
        for chunk in range(3):
            for x in range(chunk * 3, (chunk * 3) + 3):
                text = Text(self.get_cell_str(x, y))
                if (x, y) in green:
                    text.stylize("bold green")
                if (x, y) in red:
                    text.stylize("bold red")
                retval += text
                if not compact:
                    retval += "|"
            retval += "║"
        console.print(retval)
        if y == 8:
            if compact:
                print("╚═══╩═══╩═══╝")
            else:
                print("╚═╧═╧═╩═╧═╧═╩═╧═╧═╝")
            return
        if y % 3 in (0, 1):
            if not compact:
                print("╟─┼─┼─╫─┼─┼─╫─┼─┼─╢")
        else:
            if compact:
                print("╠═══╬═══╬═══╣")
            else:
                print("╠═╪═╪═╬═╪═╪═╬═╪═╪═╣")

    def print_board(self, compact=True, green=None, red=None):
        for y in range(9):
            self.print_board_line(y, compact=compact, green=green, red=red)


class Cell:

    def __init__(self, board: Board, x: int, y: int, value: int = None):
        self.value = value
        self.board = board
        self.x = x
        self.y = y
        if self.value is not None:
            self.possibles = set()
        else:
            self.possibles = set(range(1, 10))

    def __str__(self) -> str:
        if self.value is None:
            return f"({self.x}, {self.y})"
        return f"({self.x}, {self.y}) = {self.value}"

    def __eq__(self, other):
        if not isinstance(other, Cell):
            return NotImplementedError
        return self.value == other.value and self.x == other.x and self.y == other.y

    def clone(self, new_board: Board = None) -> 'Cell':
        if new_board is None:
            new_board = self.board
        return Cell(board=new_board, x=self.x, y=self.y, value=self.value)

    def clear(self):
        self.value = None
        self.possibles = set(range(1, 10))

    def get_chunk_number(self) -> int:
        return (self.y // 3) * 3 + (self.x // 3)

    def get_possible_values(self) -> set:
        if self.value is not None:
            self.possibles = set()
            return self.possibles
        else:
            self.possibles = set(range(1, 10))
        row = self.board.get_row(self.y)
        col = self.board.get_column(self.x)
        chunk = self.board.get_chunk(self.get_chunk_number())
        not_possibles = set(row) | set(col) | set(chunk)
        self.possibles = self.possibles - not_possibles
        return self.possibles


if __name__ == "__main__":
    board_string = ".1..7..5.8..1..7434...3.2..7...13..6..16.....368..4.79.873.596.93..2.8....589.4.7"
    board = Board(board_string)
    board.solve()
