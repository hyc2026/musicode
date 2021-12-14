

class ErrorCollector:


    def __init__(self):
        """Initialize the ErrorCollector with no issues to report."""
        self.issues = []

    def add(self, issue):
        """Add the given error or warning (CompilerError) to list of errors."""
        self.issues.append(issue)
        self.issues.sort()

    def ok(self):
        """Return True iff there are no errors."""
        return not any(not issue.warning for issue in self.issues)

    def show(self):  # pragma: no cover
        """Display all warnings and errors."""
        for issue in self.issues:
            print(issue)

    def clear(self):
        """Clear all warnings and errors. Intended only for testing use."""
        self.issues = []


error_collector = ErrorCollector()


class Position:


    def __init__(self, file, line, col, full_line):
        """Initialize Position object."""
        self.file = file
        self.line = line
        self.col = col
        self.full_line = full_line

    def __add__(self, other):
        """Increment Position column by one."""
        return Position(self.file, self.line, self.col + 1, self.full_line)


class Range:
    """Class representing a continuous range between two positions.

    start (Position) - start position, inclusive
    end (Position) - end position, inclusive
    """

    def __init__(self, start, end=None):
        """Initialize Range objects."""
        self.start = start
        self.end = end or start

    def __add__(self, other):
        """Add Range objects by concatenating their ranges."""
        return Range(self.start, other.end)


class CompilerError(Exception):


    def __init__(self, descrip, range=None, warning=False):

        self.descrip = descrip
        self.range = range
        self.warning = warning

    def __str__(self):  # pragma: no cover
        """Return a pretty-printable statement of the error.

        Also includes the line on which the error occurred.
        """
        error_color = "\x1B[31m"
        warn_color = "\x1B[33m"
        reset_color = "\x1B[0m"
        bold_color = "\033[1m"

        color_code = warn_color if self.warning else error_color
        issue_type = "warning" if self.warning else "error"

        # A position range is provided, and this is output to terminal.
        if self.range:

            # Set "indicator" to display the ^^^s and ---s to indicate the
            # error location.
            indicator = warn_color
            indicator += " " * (self.range.start.col - 1)

            if (self.range.start.line == self.range.end.line and
                 self.range.start.file == self.range.end.file):

                if self.range.end.col == self.range.start.col:
                    indicator += "^"
                else:
                    indicator += "-" * (self.range.end.col -
                                        self.range.start.col + 1)

            else:
                indicator += "-" * (len(self.range.start.full_line) -
                                    self.range.start.col + 1)

            indicator += reset_color
            return (f"{bold_color}{self.range.start.file}:"
                    f"{self.range.start.line}:{self.range.start.col}: "
                    f"{color_code}{issue_type}:{reset_color} {self.descrip}\n"
                    f"  {self.range.start.full_line}\n"
                    f"  {indicator}")
        # A position range is not provided and this is output to terminal.
        else:
            return (f"{bold_color}shivyc: {color_code}{issue_type}:"
                    f"{reset_color} {self.descrip}")

    def __lt__(self, other):  # pragma: no cover
        """Provides sort order for printing errors."""

        # everything without a range comes before everything with range
        if not self.range:
            return bool(other.range)

        # no opinion between errors in different files
        if self.range.start.file != other.range.start.file:
            return False

        this_tuple = self.range.start.line, self.range.start.col
        other_tuple = other.range.start.line, other.range.start.col
        return this_tuple < other_tuple
