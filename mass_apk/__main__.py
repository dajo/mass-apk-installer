import os
import sys
import time
import argparse


from mass_apk import _logger as log, adb
from mass_apk.commands import restore, back_up


def parse_args() -> argparse.Namespace:
    """Argument parser for mass-apk"""
    parser = argparse.ArgumentParser(prog="mass_apk")
    subparsers = parser.add_subparsers(
        title="commands", dest="command", required=True, help="help for commands"
    )

    # create sub parser for the "backup" command
    backup_sub = subparsers.add_parser("backup", help="backup help")
    backup_sub.add_argument(
        "-f",
        "--flag",
        type=adb.Flag,
        default=adb.Flag.USER,
        help="Specify which apks to backup. Defaults to  user apks."
        "Can be overriden to back up system apks with SYS or all apks with ALL",
    )

    backup_sub.add_argument(
        "-p",
        "--path",
        type=str,
        default=os.getcwd(),
        help="Folder or Path on filesystem to save back up",
    )
    backup_sub.add_argument(
        "-a",
        "--archive",
        action="store_true",
        help="compress back up folder into zip file",
    )

    # create the parser for the "restore" command
    restore_sub = subparsers.add_parser("restore", help="help for restore")
    restore_sub.add_argument(
        "-p",
        "--path",
        type=str,
        required=True,
        help="Back up File or Folder to restore from",
    )

    restore_sub.add_argument(
        "-c",
        "--clean",
        action="store_true",
        help="remove back up File or Folder defined in --path after restoration is completed ",
    )

    return parser.parse_args()


def main(args: argparse.Namespace):

    log.info("Apk Mass Installer Utility Version: 0.3.1\n")

    # kill any instances of adb-server before starting
    adb.stop_server()

    # wait for adb-server to detect phone
    while not (state := adb.state):
        time.sleep(1)

    adb.start_server()

    if args.command == "backup":
        back_up(args.path, args.flag, args.archive)
    elif args.command == "restore":
        restore(args.path, args.clean)
    else:
        sys.exit(f"Unknown command {args.command}")

    adb.stop_server()


if __name__ == "__main__":
    args = parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        log.info("Received SIGINT. Quit")
