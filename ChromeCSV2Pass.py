#!/usr/bin/env python3

# Copyright 2019 Gabriel Moura <gabriel.all@yandex.com>

import sys
import csv
import argparse
from subprocess import Popen, PIPE


class ChromeCSVArgParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser class which prints the full usage message if the
    input file is not provided.
    """
    def error(self, message):
        print(message, file=sys.stderr)
        self.print_help()
        sys.exit(2)


def pass_import_entry(path, data):
    """Import new password entry to password-store using pass insert command"""
    proc = Popen(['pass', 'insert', '--multiline', path], stdin=PIPE,
                 stdout=PIPE)
    proc.communicate(data.encode('utf8'))
    proc.wait()


def confirmation(prompt):
    """
    Ask the user for 'y' or 'n' confirmation and return a boolean indicating
    the user's choice. Returns True if the user simply presses enter.
    """

    prompt = '{0} {1} '.format(prompt, '(Y/n)')

    while True:
        user_input = input(prompt)

        if len(user_input) > 0:
            first_char = user_input.lower()[0]
        else:
            first_char = 'y'

        if first_char == 'y':
            return True
        elif first_char == 'n':
            return False

        print('Please enter y or n')


def insert_file_contents(filename, preparation_args):
    """ Read the file and insert each entry """

    entries = []

    with open(filename, 'r') as csv_in:
        next(csv_in)
        csv_out = (line for line in csv.reader(csv_in, dialect='excel'))
        for row in csv_out:
            path, data = prepare_for_insertion(row, **preparation_args)
            if path and data:
                entries.append((path, data))

    if len(entries) == 0:
        return

    print('Entries to import:')

    for (path, data) in entries:
        print(path)

    if confirmation('Proceed?'):
        for (path, data) in entries:
            pass_import_entry(path, data)
            print(path, 'imported!')


def prepare_for_insertion(row, name_is_username=True, convert_to_lower=False,
                          exclude_groups=None, prefix_name=False):
    """Prepare a CSV row as an insertable string"""
    name = escape(row[0])

    if prefix_name:
        prefix ='Chrome'
        group_components = prefix.split('/')[:1]
        path = '/'.join(group_components+[name])
    else:
        path = '/'.join([name])

    if convert_to_lower:
        path = path.lower()
    username = row[2]
    password = row[3]
    url = row[1]
    notes = None

    if username and name_is_username:
        path += '/' + username

    data = '{}\n'.format(password)

    if username:
        data += 'user: {}\n'.format(username)

    if url:
        data += 'url: {}\n'.format(url)

    if notes:
        data += 'notes: {}\n'.format(notes)

    return path, data


def escape(str_to_escape):
    """ escape the list """
    return str_to_escape.replace(" ", "-")\
                        .replace("&", "and")\
                        .replace("[", "")\
                        .replace("]", "")


def main():
    description = 'Import pass entries from an exported Google Chrome CSV file.'
    parser = ChromeCSVArgParser(description=description)

    parser.add_argument('--exclude_groups', nargs='+',
                        help='Groups to exclude when importing')
    parser.add_argument('--to_lower', action='store_true',
                        help='Convert group and name to lowercase')
    parser.add_argument('--name_is_original', action='store_true',
                        help='Use the original entry name instead of the '
                             'username for the pass entry')
    parser.add_argument('--prefix','-p', action='store_true',
                        help='Add Chrome to prefix')

    parser.add_argument('input_file', help='The CSV file to read from')

    args = parser.parse_args()

    preparation_args = {
        'convert_to_lower': args.to_lower,
        'name_is_username': not args.name_is_original,
        'exclude_groups': args.exclude_groups,
        'prefix_name': args.prefix
    }

    input_file = args.input_file
    print("File to read:", input_file)
    insert_file_contents(input_file, preparation_args)


if __name__ == '__main__':
    main()