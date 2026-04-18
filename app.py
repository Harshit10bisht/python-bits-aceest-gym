"""Flask HTTP API for ACEest Fitness & Gym management."""

from __future__ import annotations

import os
import sqlite3

from flask import Flask, Response, g, jsonify, request

from fitness_core import (
    PROGRAMS,
    WORKOUTS,
    compute_calories,
    init_db,
    progress_week_label,
    workouts_for,
)


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["ACEEST_DB"] = db_path or os.environ.get("ACEEST_DB", "aceest_fitness.db")
    init_db(app.config["ACEEST_DB"])

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            conn = sqlite3.connect(app.config["ACEEST_DB"])
            conn.row_factory = sqlite3.Row
            g.db = conn
        return g.db

    @app.teardown_appcontext
    def close_db(_: BaseException | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.get("/health")
    def health() -> Response:
        return jsonify({"status": "ok"})

    @app.get("/version")
    def version() -> Response:
        return jsonify({"version": os.environ.get("APP_VERSION", "v2")})

    @app.get("/workouts")
    def list_all_workouts() -> Response:
        return jsonify(WORKOUTS)

    @app.get("/workouts/<program>")
    def list_program_workouts(program: str) -> tuple[Response, int]:
        try:
            return jsonify({"program": program, "workouts": workouts_for(program)}), 200
        except KeyError:
            return jsonify({"error": f"Unknown program: {program}"}), 404

    @app.get("/programs")
    def list_programs() -> Response:
        return jsonify(
            [{"name": name, "factor": data["factor"]} for name, data in PROGRAMS.items()]
        )

    @app.post("/clients")
    def create_or_update_client() -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        program = (data.get("program") or "").strip()
        if not name or not program:
            return jsonify({"error": "Name and Program required"}), 400
        if program not in PROGRAMS:
            return jsonify({"error": f"Unknown program: {program}"}), 400

        try:
            age = int(data.get("age", 0))
            weight = float(data.get("weight", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "age must be int and weight a number"}), 400

        calories = compute_calories(weight, program)
        db = get_db()
        try:
            db.execute(
                """
                INSERT OR REPLACE INTO clients (name, age, weight, program, calories)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, age, weight, program, calories),
            )
            db.commit()
        except sqlite3.Error as e:
            return jsonify({"error": str(e)}), 500

        return (
            jsonify(
                {
                    "name": name,
                    "age": age,
                    "weight": weight,
                    "program": program,
                    "calories": calories,
                }
            ),
            201,
        )

    @app.get("/clients/<name>")
    def get_client(name: str) -> tuple[Response, int]:
        row = get_db().execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
        if row is None:
            return jsonify({"error": "Client not found"}), 404
        return (
            jsonify(
                {
                    "name": row["name"],
                    "age": row["age"],
                    "weight": row["weight"],
                    "program": row["program"],
                    "calories": row["calories"],
                }
            ),
            200,
        )

    @app.post("/clients/<name>/progress")
    def save_progress(name: str) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        try:
            adherence = int(data.get("adherence", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "adherence must be an integer"}), 400
        if not 0 <= adherence <= 100:
            return jsonify({"error": "adherence must be between 0 and 100"}), 400

        week = progress_week_label()
        db = get_db()
        db.execute(
            "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
            (name, week, adherence),
        )
        db.commit()
        return jsonify({"client_name": name, "week": week, "adherence": adherence}), 201

    return app


if __name__ == "__main__":
    create_app().run(
        host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False
    )
