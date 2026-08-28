#!/usr/bin/env python3
"""Command-line entry point.

Το project είναι το ίδιο το πακέτο `dideman`, οπότε ο γονικός κατάλογος
πρέπει να βρίσκεται στο sys.path για να λυθεί το `dideman.settings`.
"""
import os
import sys


def main():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dideman.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
