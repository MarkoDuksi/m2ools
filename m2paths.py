#!/usr/bin/env python
# coding: utf-8

import os
import re
from datetime import datetime


def get_new_path(*args, extension='', dirname='', timestamp=False,
                 replacewith='', createdir=False,
                 timeformat='%Y-%m-%d_%H%M%S'):
    """A possibly-sanitized path pieced together from supplied arguments.

    Parameters
    ----------
    *args : object(s) implementing the `__str__()` method, default=''
        Non-empty string representations of all positional arguments are
        joined on '_'. This constitutes the first part of the file name.
    extension : an object implementing the `__str__()` method, default=''
        The string, if not emtpty, is prepended by '.' unless already
        starting with at least one '.'. This constitutes the last part of
        the file name.
    dirname : an object implementing the `__str__()` method, default=''
        The directory structure part of the path.
    timestamp : bool, default=False
        Setting this to True appends a current time timestamp as the
        middle part of the file name, joined on '_'.
    replacewith : str or None, default=''
        Setting this to `None` disables sanitization. Setting this to a
        non-empty string value forces sanitizer to use it in place
        of any one (or more consecutive) unwanted characters. The
        `replacewith` value itself is sanitized before use (see notes).
    createdir : bool, default=False
        Setting this to True creates a directory structure if it does
        not already exist.
    timeformat : str, default='%Y%m%d-%H%M%S'
        As accepted by datetime.datetime.strftime().

    Returns
    -------
    str
        A non-empty path string composed of (both optional per se) the
        sanitized directory structure part and the sanitized file name
        part. The parts are joined on the running operating system's path
        separator character.
    None
        Instead of an empty string which may result from lacking any of
        allowed characters or `replacewith` value in all positional as
        well as in 'extension` and `dirname` keyword arguments while
        `timestamp` is set to False.

    Notes
    -----
    The path is sanitized by disallowing the following characters depending
    on the part of the path they appear in:
    - in the file name part the unwanted characters are: '\', '/', '\n',
    '\r' and '\0'
    - in the directory structure part the unwanted characters are the same
    with an exception of the running operating system's path separator
    character.

    The `replacewith` value is sanitized as if being a part of the file
    name, using the default (empty string) `replacewith` value.

    Examples
    --------
    >>> get_new_path('test-file-name', dirname='test-dir/test-subdir',
    ...              extension='csv', timestamp=True, createdir=True)
    test-dir/test-subdir/test-file-name_20210927-141159.csv    # variable

    >>> file_name_main_parts = ['Europe', 'Croatia', 'Zagreb']
    >>> get_new_path(*file_name_main_parts, dirname='test-dir/test-subdir2',
                     extension='csv', createdir=True)
    test-dir/test-subdir2/Europe_Croatia_Zagreb.csv

    >>> tainted_file_name_parts = ['Europe/Europa', 'Croatia/Hrvatska',
    ...                            'Zagreb/Zagreb']
    >>> get_new_path(*tainted_file_name_parts,
    ...              dirname='test-dir/test-subdir',
    ...              extension='csv', replacewith='-')
    test-dir/test-subdir/Europe-Europa_Croatia-Hrvatska_Zagreb-Zagreb.csv
    """

    if replacewith is not None:
        replacewith = untaint('file', replacewith)
    dirname = untaint('dir', str(dirname), replacewith=replacewith)
    extension = untaint('file', str(extension), replacewith=replacewith)
    if createdir and dirname:
        os.makedirs(dirname, exist_ok=True)
    if extension and not extension.startswith('.'):
        extension = '.' + extension
    timestamp = (datetime.now().strftime(timeformat),) if timestamp else ()
    args += timestamp
    filename = untaint('file', '_'.join([str(arg) for arg in args]),
                       replacewith=replacewith) + extension
    return os.path.join(dirname, filename)


def untaint(mode, name, replacewith=''):
    """Replace unwanted characters from `name` by `replacewith`.

    Return a possibly-empty string derived from `name` according to rules
    below or raise a ValueError if provided an invalid argument.

    If `mode` is 'file', the unwanted characters are: '~', '\', '/', '\n',
    '\r' and '\0'. If `mode` is 'dir', the unwanted characters are the same
    with an exception of the running operating system's path separator
    character. If `mode` is `None`, the `name` is returned unchanged.
    """

    if replacewith is None:
        return name

    if mode == 'file':
        replace_re = r'([~/\n\r\0\\]+)'
    elif mode == 'dir':
        if os.path.sep == '/':
            replace_re = r'([~\n\r\0\\]+)'
        else:
            replace_re = r'([~/\n\r\0]+)'
    else:
        raise ValueError

    return re.sub(replace_re, f'{replacewith}', str(name))


def main_test():
    print('Return None if nothing is asked for:')
    print(get_new_path())

    print('Return only the directory structure with no file name part:')
    print(get_new_path(dirname='test-dir/test-subdir'))

    print('Return only the file name with no directory structure part:')
    print(get_new_path('test-file-name', extension='csv'))

    print('Return both the directory structure and file name (with timestamp):')
    print(get_new_path('test-file-name', dirname='test-dir/test-subdir', extension='.csv', timestamp=True))
    print(get_new_path(timestamp=True, extension='.csv'))

    print('Try to return a broken file path without a substitute replacewith:')
    print(get_new_path('test-br\n\0\r\o\\k\\\e\\\\n/-file-name',
                       0,
                       42,
                       3.14,
                       False,
                       str,
                       extension='csv',
                       timestamp=True,
                       dirname='test-br\n\0\r\o\\k\\\e\\\\n/dir-name',
                       replacewith=''))

    print('Try to return the same broken file path with "(!)" in place of unwanted characters:')
    print(get_new_path('test-br\n\0\r\o\\k\\\e\\\\n/-file-name',
                       0,
                       42,
                       3.14,
                       False,
                       str,
                       extension='csv',
                       timestamp=True,
                       dirname='test-br\n\0\r\o\\k\\\e\\\\n/dir-name',
                       replacewith='(X)'))


def docstring_test():
    print(get_new_path('test-file-name', dirname='test-dir/test-subdir',
                       extension='csv', timestamp=True, createdir=True))

    file_name_main_parts = ['Europe', 'Croatia', 'Zagreb']
    print(get_new_path(*file_name_main_parts, dirname='test-dir/test-subdir2',
                       extension='csv', createdir=True))

    tainted_file_name_parts = ['Europe/Europa', 'Croatia/Hrvatska', 'Zagreb/Zagreb']
    print(get_new_path(*tainted_file_name_parts, dirname='test-dir/test-subdir',
                       extension='csv', replacewith='-'))


if __name__ == '__main__':
    main_test()

    print()
    docstring_test()
