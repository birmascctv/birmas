from fastapi import APIRouter
from ..db import get_connection

router = APIRouter()

@router.get("/stats/counts")
def get_counts(camera_id: str, interval: str = "1h"):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT date_trunc(%s, ts) as bucket, COUNT(*)
            FROM events
            WHERE camera_id = %s
            GROUP BY bucket
            ORDER BY bucket DESC
            LIMIT 24
        """, (interval, camera_id))
        rows = cur.fetchall()
    return {
        "labels": [r[0].isoformat() for r in rows],
        "counts": [r[1] for r in rows]
    }
