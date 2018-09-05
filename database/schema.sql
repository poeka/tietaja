DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS game;
DROP TABLE IF EXISTS match;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL UNIQUE,
  password TEXT NOT NULL
);

CREATE TABLE game (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  game_id INTEGER UNIQUE NOT NULL,
  creator TEXT NOT NULL
);

CREATE TABLE match
(
  id INTEGER PRIMARY KEY,
  match_id TEXT NOT NULL,
  game_id INTEGER NOT NULL
);
