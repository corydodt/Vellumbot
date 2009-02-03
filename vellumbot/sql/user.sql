BEGIN;

CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    name varchar(100)
);

CREATE TABLE alias (
    userId INTEGER references user(id),
    words varchar(255),
    expression varchar(255),
    PRIMARY KEY (userId, words)
);


COMMIT;
