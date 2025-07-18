-- SQLite or Postgres—works the same except for UUID
-- (SQLite: SQLAlchemy handles uuid TEXT under the hood)

create table players (
    id          text primary key,
    player_name text    not null,
    heat        integer not null,
    division    text    not null,
    dropped_out boolean not null default false,
    active      boolean not null default true
);

create table prop_universe (
    id        uuid primary key,
    prop_name text    not null unique,
    active    boolean not null default true
);

create table advance_bets (
    bet_id     text primary key,
    player_id  text not null references players(id),
    bettor_email TEXT NOT NULL,
    amount     real not null check(amount > 0),
    placed_at  datetime default current_timestamp
);

create table win_bets (
    bet_id    uuid primary key,
    player_id uuid not null references players(id),
    amount    real not null,
    placed_at datetime default current_timestamp
);

create table prop_bets (
    bet_id    uuid primary key,
    prop_id   uuid not null references prop_universe(id),
    side_yes  boolean not null,  -- TRUE = Yes
    amount    real not null,
    placed_at datetime default current_timestamp
);
