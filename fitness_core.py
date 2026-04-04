"""Core domain logic and database setup for ACEest Fitness (ported from Aceestver2.0.1 baseline)."""

from __future__ import annotations

import sqlite3
from datetime import datetime

PROGRAMS: dict[str, dict[str, float]] = {
    "Fat Loss (FL)": {"factor": 22},
    "Muscle Gain (MG)": {"factor": 35},
    "Beginner (BG)": {"factor": 26},
}


def compute_calories(weight_kg: float, program_name: str) -> int:
    if program_name not in PROGRAMS:
        raise KeyError(f"Unknown program: {program_name}")
    return int(weight_kg * PROGRAMS[program_name]["factor"])


def progress_week_label(when: datetime | None = None) -> str:
    dt = when if when is not None else datetime.now()
    return dt.strftime("Week %U - %Y")


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                age INTEGER,
                weight REAL,
                program TEXT,
                calories INTEGER
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                week TEXT,
                adherence INTEGER
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
