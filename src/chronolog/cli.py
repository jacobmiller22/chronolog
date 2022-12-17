
""" Imports for cli """
from datetime import datetime
import argparse
import sys
import os
import re
import json
from chronolog.chronolog import ChronologApp


def query_string(question: str, default=None) -> str:
    """ Queries the user for a string """

    default_text = f" (default: {default})" if default is not None else ""
    print(f"{question}{default_text}")
    string = None
    while string is None:
        try:
            string = input("Enter a string: ")
            if string == "" and default is not None:
                return default
        except KeyboardInterrupt:
            # Exit gracefully
            sys.exit(0)
        except:
            print("Error: Unknown error")
            sys.exit(1)

    return string


def query_choices(question: str, choices: list, default=None) -> str:
    """ Queries the user for a choice from a list of choices """

    # Display the choices
    default_text = f" (default: {default})" if default is not None else ""
    print(f"{question}{default_text}")
    for i, choice in enumerate(choices):
        print(f"{i + 1}. {choice}")

    # Get the choice
    choice = None
    while choice is None:
        try:
            choice = input(f"Valid choices are 1-{len(choices)}: ")
            if choice == "" and default is not None:
                return default
            else:
                choice = int(choice)
        except ValueError:

            print(
                f"Please enter a number{' or nothing to use the default' if default is not None else ''}")
            continue

        if choice < 1 or choice > len(choices):
            print("Please enter a valid number for your choice")
            choice = None

    return choices[choice - 1]


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
            print("")  # Add a newline after Ctrl+D
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
    parser.add_argument("-f", "--input-path", required=False,
                        help="The path to the file to use as input for the log. Defaults to the standard input.")

    parser.add_argument("-c", "--config", required=False,
                        help="The path to the configuration file. Defaults to the standard configuration file.")

    # Add subparsers for the different commands
    subparsers = parser.add_subparsers(dest="subcommand", title="subcommands")

    configure_parser = subparsers.add_parser(
        "configure", help="Configure the chronolog application")
    configure_parser.add_argument("-o", "--output", required=False,
                                  help="The path where the configuration file will be created. Defaults to the location: '~/.chronolog'.")
    configure_parser.add_argument("-D", "--destination", required=False, choices=[
                                  "google_drive"], help="The destination party for the logs. Defaults to google_drive.")

    args = parser.parse_args()

    # Check the config file
    if args.config is None:
        args.config = os.path.join(os.path.expanduser(
            "~"), ".chronolog", "config.json")

    # Check if the config file exists, and if not, prompt the user to create it with the configure command
    if not os.path.exists(args.config) and args.subcommand != "configure":
        print("Error: Could not find configuration file, please run the configure command to create it.")
        sys.exit(1)

    # If the date is not provided, use today
    date = args.date
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

    # Check the subparsers
    if args.subcommand == "configure":
        # Check the output path
        if args.output is None:
            args.output = os.path.join(os.path.expanduser("~"), ".chronolog")

    # Update the args with the adjusted values
    args.date = date
    args.input_path = input_path

    return vars(args)


def configure(args):
    """ Configures the chronolog application """

    output_path = args.get("output")

    # Check if the output path exists
    if not os.path.exists(output_path):
        # Create the directory
        os.makedirs(output_path)

    # Check if the output path is a directory
    if not os.path.isdir(output_path):
        print("Error: The output path is not a directory")
        sys.exit(1)

    # Check if the output path is writable
    if not os.access(output_path, os.W_OK):
        print("Error: The output path is not writable")
        sys.exit(1)

    # Check if the configuration file already exists
    config = {}
    config_path = os.path.join(output_path, "config.json")
    if os.path.exists(config_path):
        proceed = query_yes_no(
            "A configuration file already exists at the specified location. Would you like to overwrite it?")
        if not proceed:
            print("Goodbye!")
            sys.exit(0)
        # Load the configuration file
        with open(config_path, "r") as f:
            config = json.load(f)

    # Get the configuration from the user

    # Ask the user for their preferred grouping method
    valid_grouping_methods = ["daily", "weekly", "monthly", "yearly"]
    default_grouping_method = args.get("grouping")
    if default_grouping_method is None:
        default_grouping_method = query_choices(
            "Enter the default grouping frequency. This affects how the logs will be separated. Destinations can have different grouping frequency", valid_grouping_methods, default=(config.get("grouping") or "monthly"))
    elif default_grouping_method not in valid_grouping_methods:
        print("Error: Invalid grouping method")
        sys.exit(1)
    config['grouping'] = default_grouping_method

    # Ask the user for their preferred destination
    valid_destinations = ["google_drive"]
    destination = args.get("destination")
    if destination is None:
        destination = query_choices(
            "Enter the destination for the logs.", valid_destinations, default=(config.get("destination") or "google_drive"))
    elif destination not in valid_destinations:
        print("Error: Invalid destination")
        sys.exit(1)
    config['destination'] = destination
    config[destination] = config.get(destination) or {}

    # Destination specific configuration
    if destination == "google_drive":
        # Ask the user for the path in their google drive
        default_path = (None or config.get(destination).get("path"))
        # Pretty the default path
        if default_path is not None:
            default_path = os.path.normpath(os.path.join(*default_path))
        path = query_string(
            "Enter the path to the Google Drive folder where the logs will be stored, including the name of the drive (My Drive, <shared_drive_name>, etc.)", default=default_path)

        # Split path by '/' or '\' or csv and remove empty strings
        path = list(filter(None, re.split(r'[/\\,]', path)))
        config[destination]["path"] = path

        # Ask if this is a shared drive
        config[destination]["is_shared_drive"] = query_yes_no(
            "Is this a shared drive?", default=(False or config.get(
                destination).get("is_shared_drive")))

        # Clear the _parents_path if it exists
        if "_parents_path" in config[destination]:
            del config[destination]["_parents_path"]

    # Ask if they want to change their grouping method specifically for the destination
    config[destination]['grouping'] = query_choices(
        f"Enter the grouping frequency for destination '{destination}'. This affects how the logs will be separated.", valid_grouping_methods, default=config.get("grouping"))

    # Write the configuration file
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)


def main() -> int:
    """ Main entry point of the Chronolog CLI """

    # Parse the command line arguments
    args: dict = parse_args()

    # Check the subcommand
    if args.get("subcommand") == "configure":
        configure(args)
        return 0

    # Determine the date to log
    date: datetime = args.get("date")

    # Create the Chronolog object
    app = ChronologApp(dest="google_drive", path_to_config=args.get("config"))

    # Read the input file")
    print(f"Logging for {date.strftime('%Y-%m-%d')}")
    log_contents = read_input(args.get("input_path"))

    # Upload the log
    success = app.upload_log(date, log_contents)

    if success:
        # Display a success message and exit
        print(f"Successfully logged the day: {date.strftime('%Y-%m-%d')}")
    else:
        # Display an error message and exit
        print(f"Failed to log the day: {date.strftime('Y-%m-%d')}")

    print("Goodbye!")
    return not success


if __name__ == "__main__":
    main()
