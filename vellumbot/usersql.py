"""
An ugly kludge because store.execute() does not accept an sql script.  Put the
whole script in a python file so Python code can run it.

I sad.
"""
import sys

SQL_SCRIPT = ['''
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    name varchar(100)
);
''',

'''CREATE TABLE alias (
    userId INTEGER references user(id),
    words varchar(255),
    expression varchar(255),
    PRIMARY KEY (userId, words)
);
''',
]

def run(argv=None):
    if argv is None:
        argv = sys.argv
    for line in SQL_SCRIPT:
        print line

if __name__ == '__main__':
    sys.exit(run())
