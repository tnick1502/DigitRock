CREATE TABLE IF NOT EXISTS "users" (
  "user_ip" cidr PRIMARY KEY,
  "username" varchar(50)
);

CREATE TABLE IF NOT EXISTS "sessions" (
  "session_id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY NOT NULL,
  "user_ip" cidr,
  "session_start" timestamp,
  "session_end" timestamp,
  "object_number" varchar(10),
  "test_type" varchar(100),
  "report_count" int,
  "program_version" float
);

CREATE TABLE IF NOT EXISTS "use_count" (
  "use_id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY NOT NULL,
  "user_ip" cidr,
  "parameter_name" varchar(100),
  "datetime" timestamp,
  "object_number" varchar(10),
  "test_type" varchar(100),
  "program_version" float
);

CREATE INDEX idx_sessions_test_type on sessions (test_type);
CREATE INDEX idx_use_count_parameter_name on use_count (parameter_name);

SELECT session_end, session_start,
ROUND( CAST( EXTRACT ( EPOCH FROM (session_end - session_start)) AS numeric), 1) AS duration,
ROUND( CAST( EXTRACT(EPOCH FROM (session_end - session_start)) / report_count AS numeric), 1) AS report_time FROM sessions


SELECT test_type,
ROUND (CAST (AVG (EXTRACT (EPOCH FROM (session_end - session_start))) AS numeric), 1) AS avg_duration,
ROUND (CAST (AVG ( EXTRACT(EPOCH FROM (session_end - session_start)) / report_count) AS numeric), 1) AS avg_report_time
FROM sessions
GROUP BY test_type


CREATE OR REPLACE FUNCTION get_avg_by_user (current_username varchar, current_year int, current_month int)
RETURNS TABLE (test_type varchar, avg_session_duration numeric, avg_report_time numeric) AS $$
	SELECT test_type,
	ROUND (CAST (AVG (EXTRACT (EPOCH FROM (session_end - session_start))) AS numeric), 1) AS avg_duration,
	ROUND (CAST (AVG ( EXTRACT(EPOCH FROM (session_end - session_start)) / report_count) AS numeric), 1) AS avg_report_time
	FROM sessions
	LEFT JOIN users USING (user_ip)
	WHERE username = current_username AND EXTRACT(MONTH FROM session_start) = current_month AND EXTRACT(YEAR FROM session_start) = current_year
	GROUP BY test_type
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_avg_by_test_type (current_year int, current_month int)
RETURNS TABLE (test_type varchar, avg_session_duration numeric, avg_report_time numeric) AS $$
	SELECT test_type,
	ROUND (CAST (AVG (EXTRACT (EPOCH FROM (session_end - session_start))) AS numeric), 1) AS avg_duration,
	ROUND (CAST (AVG ( EXTRACT(EPOCH FROM (session_end - session_start)) / report_count) AS numeric), 1) AS avg_report_time
	FROM sessions
	LEFT JOIN users USING (user_ip)
	WHERE EXTRACT(MONTH FROM session_start) = current_month AND EXTRACT(YEAR FROM session_start) = current_year
	GROUP BY test_type
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_sessions_by_user (current_username varchar, current_year int, current_month int)
RETURNS TABLE (test_type varchar, session_start timestamp, session_duration numeric, report_count int, object_number varchar, avg_report_time numeric) AS $$
	SELECT test_type, session_start,
	ROUND (CAST ( EXTRACT(EPOCH FROM (session_end - session_start)) AS numeric), 1) AS session_duration,
	report_count,
	object_number,
	ROUND (CAST ( EXTRACT(EPOCH FROM (session_end - session_start)) / report_count AS numeric), 1) AS avg_report_time
	FROM sessions
	LEFT JOIN users USING (user_ip)
	WHERE username = current_username AND EXTRACT(MONTH FROM session_start) = current_month AND EXTRACT(YEAR FROM session_start) = current_year
$$ LANGUAGE SQL;