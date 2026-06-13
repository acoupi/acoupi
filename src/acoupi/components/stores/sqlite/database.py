"""Schema helpers for the sqlite metadata store."""

import sqlite3

SCHEMA_VERSION = 1


def create_base_schema(
    connection: sqlite3.Connection,
    version: int = SCHEMA_VERSION,
) -> None:
    """Create the metadata-store schema if it does not exist."""
    connection.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS deployment (
            id BLOB PRIMARY KEY,
            name TEXT NOT NULL,
            started_on TEXT NOT NULL UNIQUE,
            ended_on TEXT,
            latitude REAL,
            longitude REAL
        );

        CREATE TABLE IF NOT EXISTS recording (
            id BLOB PRIMARY KEY,
            path TEXT UNIQUE,
            datetime TEXT NOT NULL UNIQUE,
            duration_s REAL NOT NULL,
            samplerate_hz INTEGER NOT NULL,
            audio_channels INTEGER NOT NULL DEFAULT 1,
            deployment_id BLOB NOT NULL,
            FOREIGN KEY (deployment_id) REFERENCES deployment(id)
        );

        CREATE TABLE IF NOT EXISTS model_output (
            id BLOB PRIMARY KEY,
            model_name TEXT NOT NULL,
            recording_id BLOB NOT NULL,
            created_on TEXT NOT NULL,
            FOREIGN KEY (recording_id) REFERENCES recording(id)
        );

        CREATE TABLE IF NOT EXISTS detection (
            id BLOB PRIMARY KEY,
            prediction_type TEXT NOT NULL CHECK (
                prediction_type IN ('presence', 'sequence', 'event')
            ),
            start_time_s REAL,
            end_time_s REAL,
            low_freq_hz REAL,
            high_freq_hz REAL,
            detection_score REAL NOT NULL,
            model_output_id BLOB NOT NULL,
            FOREIGN KEY (model_output_id) REFERENCES model_output(id)
        );

        CREATE TABLE IF NOT EXISTS predicted_tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            detection_id BLOB NOT NULL,
            FOREIGN KEY (detection_id) REFERENCES detection(id)
        );

        CREATE INDEX IF NOT EXISTS idx_recording_deployment_id
        ON recording(deployment_id);

        CREATE INDEX IF NOT EXISTS idx_model_output_recording_id
        ON model_output(recording_id);

        CREATE INDEX IF NOT EXISTS idx_model_output_created_on
        ON model_output(created_on);

        CREATE INDEX IF NOT EXISTS idx_detection_model_output_id
        ON detection(model_output_id);

        CREATE INDEX IF NOT EXISTS idx_predicted_tag_detection_id
        ON predicted_tag(detection_id);

        CREATE INDEX IF NOT EXISTS idx_predicted_tag_key_value
        ON predicted_tag(key, value);

        PRAGMA user_version = {version};
        """
    )
