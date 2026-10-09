"""Read a synthetic demo turn's SQL, records, model selection, and displayed answer."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def inspect_turn(path: Path, turn_id: str | None = None) -> None:
    """Open the specified local database read-only; print a bounded turn trace."""
    if not path.is_file():
        raise ValueError("Choose an existing synthetic demo database.")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if turn_id is None:
            row = connection.execute(
                "SELECT turn_id FROM chat_messages WHERE role = 'assistant' "
                "ORDER BY message_id DESC LIMIT 1"
            ).fetchone()
            if row is None:
                raise ValueError("No completed demo turn exists yet.")
            turn_id = row["turn_id"]
        print(f"Synthetic demo trace — turn {turn_id}")
        messages = connection.execute(
            "SELECT role, content FROM chat_messages WHERE turn_id = ? ORDER BY message_id",
            (turn_id,),
        ).fetchall()
        if not messages:
            raise ValueError("That turn was not found.")
        print("\nQUESTION\n" + messages[0]["content"])
        for row in connection.execute(
            "SELECT stage, detail_json, prompt_version FROM chat_retrieval_stages "
            "WHERE turn_id = ? ORDER BY stage_id", (turn_id,),
        ):
            detail = json.loads(row["detail_json"])
            print(f"\n{row['stage'].upper()} — prompt version {row['prompt_version']}")
            print(json.dumps(detail, indent=2, ensure_ascii=False))
            if row["stage"] == "result":
                request = detail["request"]
                direct = connection.execute(
                    "SELECT h.name, n.stay_date, n.nightly_rate_cents, n.rooms_available "
                    "FROM saved_hotels h JOIN saved_hotel_zips z ON z.hotel_id = h.hotel_id "
                    "LEFT JOIN demo_hotel_nights n ON n.hotel_id = h.hotel_id "
                    "AND n.stay_date >= ? AND n.stay_date < ? "
                    "WHERE z.postcode = ? ORDER BY h.hotel_id, n.stay_date LIMIT 701",
                    (request["check_in"], request["check_out"], request["postcode"]),
                ).fetchall()
                print("\nDIRECT SQLITE NIGHTLY ROWS (maximum 701)")
                print(json.dumps([dict(item) for item in direct], indent=2))
        for message in messages[1:]:
            print("\nDISPLAYED ANSWER\n" + message["content"])
        print("\nForeign-key violations:", len(connection.execute("PRAGMA foreign_key_check").fetchall()))
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("--turn-id", help="specific turn UUID; defaults to latest completed turn")
    args = parser.parse_args()
    inspect_turn(args.database, args.turn_id)


if __name__ == "__main__":
    main()
