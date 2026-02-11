-- Create users table for authentication
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'student',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    oauth_provider VARCHAR(50),
    google_id VARCHAR(255) UNIQUE,
    profile_picture VARCHAR(512)
);

-- Create index on google_id for OAuth
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create EEG data table  
CREATE TABLE IF NOT EXISTS eeg_data (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    raw_channels JSONB,
    delta_power DOUBLE PRECISION,
    theta_power DOUBLE PRECISION,
    alpha_power DOUBLE PRECISION,
    beta_power DOUBLE PRECISION,
    gamma_power DOUBLE PRECISION,
    theta_alpha_ratio DOUBLE PRECISION,
    beta_alpha_ratio DOUBLE PRECISION,
    signal_quality DOUBLE PRECISION,
    cognitive_state VARCHAR(50),
    eeg_fatigue_score DOUBLE PRECISION
);

-- Create hypertable for time-series data
SELECT create_hypertable('eeg_data', 'timestamp', if_not_exists => TRUE);

-- Create face data table
CREATE TABLE IF NOT EXISTS face_events (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    yawn_detected BOOLEAN DEFAULT FALSE,
    eye_closure_seconds DOUBLE PRECISION DEFAULT 0,
    face_fatigue_score DOUBLE PRECISION,  
    confidence DOUBLE PRECISION
);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    alert_level VARCHAR(50),
    fatigue_score DOUBLE PRECISION,
    eeg_contribution DOUBLE PRECISION,
    face_contribution DOUBLE PRECISION,
    trigger_reason VARCHAR(255),
    acknowledged BOOLEAN DEFAULT FALSE
);

COMMIT;