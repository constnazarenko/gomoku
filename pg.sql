SET client_encoding = 'UTF8';

DROP TABLE IF EXISTS match_moves;
DROP TABLE IF EXISTS match;

DROP SEQUENCE IF EXISTS matchid;

CREATE SEQUENCE matchid
    START WITH 1  
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE match (
	id         integer  NOT NULL DEFAULT nextval('matchid') primary key,
	black      text     NOT NULL,
	white      text,
    start_time timestamp with time zone DEFAULT now()
);

CREATE TABLE match_moves (
	match_id   integer  NOT NULL REFERENCES match(id) ON UPDATE CASCADE ON DELETE CASCADE,
    is_black   boolean  NOT NULL,
    x          integer  NOT NULL,
    y          integer  NOT NULL,
    made       timestamp with time zone DEFAULT now(),
    win        boolean DEFAULT FALSE
);


CREATE OR REPLACE FUNCTION time_to_str(intime timestamp with time zone)
    RETURNS text
    LANGUAGE sql
    IMMUTABLE STRICT
AS $function$
    select to_char($1 at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"');
$function$;
