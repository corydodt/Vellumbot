"""
An ugly kludge because store.execute() does not accept an sql script.  Put the
whole script in a python file so Python code can run it.

I sad.
"""
import sys

SQL_SCRIPT = ['''
CREATE TABLE user (
    name varchar(100),
    network varchar(100),
    encoding varchar(100),
    PRIMARY KEY (name, network)
);
''',

'''
CREATE TABLE alias (
    userName varchar(100) references user(name),
    userNetwork varchar(100) references user(network),
    words varchar(255),
    expression varchar(255),
    PRIMARY KEY (userName, userNetwork, words)
);
''',

'''
CREATE TABLE session (
    name varchar(100) PRIMARY KEY,
    encoding varchar(100)
);
''',

'''
INSERT INTO session VALUES ('#@@default@@', 'utf-8');
''',

]

def run(argv=None):
    if argv is None:
        argv = sys.argv
    for line in SQL_SCRIPT:
        print line

if __name__ == '__main__':
    sys.exit(run())
