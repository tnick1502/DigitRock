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
  "report_count" int
);

CREATE TABLE IF NOT EXISTS "use_count" (
  "use_id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY NOT NULL,
  "user_ip" cidr,
  "parameter_name" varchar(100),
  "datetime" timestamp
);

CREATE INDEX idx_sessions_test_type on sessions (test_type);
CREATE INDEX idx_use_count_parameter_name on use_count (parameter_name);