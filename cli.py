
""" Imports for cli """
from datetime import datetime
import argparse
import sys
from chronolog import ChronologApp


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".

    Taken from (and slightly modified): https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print(question + prompt, end="")
        choice = None
        try:
            choice = input().lower()
        except KeyboardInterrupt:
            # Exit gracefully
            sys.exit(0)
        if default is not None and choice == "":
            return valid[default]
        if choice in valid:
            return valid[choice]
        print(
            "Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def read_input(input_path: str) -> str:
    """ Reads the input file and returns the contents """

    # If the input path is None, use the standard input
    if input_path is None:
        print("Reading from standard input. Press Ctrl+D to finish.")
        try:
            contents = sys.stdin.read()
            print("") # Add a newline after Ctrl+D
            return contents
        except KeyboardInterrupt:
            # Exit gracefully
            sys.exit(0)
        except:
            print("Error: Unknown error")
            sys.exit(1)
    with open(input_path, "r") as input_file:
        print("Reading input file...")
        try:
            return input_file.read()
        except UnicodeDecodeError:
            print("Error: Could not read input file")
            sys.exit(1)
        except FileNotFoundError:
            print("Error: Could not find input file")
            sys.exit(1)
        except PermissionError:
            print("Error: Insufficient file permissions")
            sys.exit(1)
        except:
            print("Error: Unknown error")
            sys.exit(1)


def infer_date(date: str):
    """ Infers the date from the provided string """

    # Possible date patterns
    patterns = {"ymd": ["%Y-%m-%d",  "%m/%d/%Y", "%m/%d/%y",
                        "%m/%d/%Y", "%m/%d/%y", "%m/%d", "%m/%d/%Y", "%m/%d/%y"], "md": ["%m-%d", "%m/%d"], "d": ["%d"], "leap-md": ["%Y %m-%d", "%Y %m/%d"], "leap-d": ["%Y %m %d"]}

    def try_parse(date: str, pattern: str):
        """ Tries to parse the date with the provided pattern """
        try:
            return datetime.strptime(date, pattern)
        except ValueError:
            return None

    for pattern in patterns["ymd"]:
        inference = try_parse(date, pattern)
        if inference is not None:
            return inference

    for pattern in patterns["md"]:
        inference = try_parse(date, pattern)
        if inference is not None:
            return inference.replace(year=datetime.now().year)

    for pattern in patterns["d"]:
        inference = try_parse(date, pattern)
        if inference is not None:
            return inference.replace(year=datetime.now().year, month=datetime.now().month)

    # Add the current year in case the date is a leap day
    for pattern in patterns["leap-md"]:
        inference = try_parse(f"{datetime.now().year} {date}", pattern)
        if inference is not None:
            return inference

    for pattern in patterns["leap-d"]:

        inference = try_parse(
            f"{datetime.now().year} {datetime.now().month} {date}", pattern)
        if inference is not None:
            return inference

    # If we get here, we couldn't infer the date
    return None


def parse_args() -> dict:
    """ Parses the command line arguments and returns the args after parsing """

    parser = argparse.ArgumentParser()

    parser.add_argument("-D", "--date", required=False,
                        help="The day to log. Will try infer the date provided. Defaults to today if no date is provided.")
    parser.add_argument("-f", "--input-path", required=False, action="store_const", const=None,
                        help="The path to the file to use as input for the log. Defaults to the standard input.")

    args = parser.parse_args()

    date = args.date

    # Check the date
    if date is None:
        date = datetime.now()
    else:
        date = infer_date(date)

    if date is None:
        parser.error(
            "Invalid date or could not infer date from provided string")

    # Check if the date is in the future
    if date > datetime.now():
        if not query_yes_no(
                "Warning: The date provided is in the future. Are you sure you want to continue?"):
            sys.exit(0)

    # Check the input file
    # TODO: Implement this
    input_path = args.input_path

    return {'date': date, 'input_path': input_path}




def main():
    """ Main entry point of the Chronolog CLI """

    args = parse_args()

    # Determine the date to log
    date: datetime = args.get("date")
    
    # Create the Chronolog object
    app = ChronologApp(dest="google_drive")

    # Read the input file")
    print(f"Logging for {date.strftime('%Y-%m-%d')}")
    log_contents = read_input(args.get("input_path"))

    # Upload the log
    success = app.upload_log(date, log_contents)

    if success:
        # Display a success message and exit
        print(f"Successfully logged the day: {date.strftime('Y-%m-%d')}")
    else:
        # Display an error message and exit
        print(f"Failed to log the day: {date.strftime('Y-%m-%d')}")
    
    print("Goodbye!")
    return not success


if __name__ == "__main__":
    main()
