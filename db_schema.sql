-- Database Schema for Polygon Generator Authentication
-- PostgreSQL version

-- Table: users
-- Stores user accounts and API keys
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    api_key_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hash (64 hex chars)
    daily_limit INTEGER DEFAULT 50 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    notes TEXT  -- For admin notes about the user
);

-- Table: request_logs
-- Stores all API requests for rate limiting and analytics
CREATE TABLE IF NOT EXISTS request_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    query_text TEXT,  -- The user's polygon query (optional, for debugging)
    success BOOLEAN DEFAULT TRUE NOT NULL,
    ip_address VARCHAR(45),  -- IPv4 or IPv6
    error_message TEXT  -- If request failed, store error
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_api_key_hash ON users(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_request_logs_user_id ON request_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_request_logs_timestamp ON request_logs(request_timestamp);
CREATE INDEX IF NOT EXISTS idx_request_logs_user_timestamp ON request_logs(user_id, request_timestamp);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts with API keys for polygon generator';
COMMENT ON TABLE request_logs IS 'Request logs for rate limiting and analytics';
COMMENT ON COLUMN users.api_key_hash IS 'SHA-256 hash of the API key (never store raw keys)';
COMMENT ON COLUMN users.daily_limit IS 'Maximum requests allowed per 24-hour rolling window';
COMMENT ON COLUMN request_logs.request_timestamp IS 'When the request was made (used for 24-hour rate limiting)';

