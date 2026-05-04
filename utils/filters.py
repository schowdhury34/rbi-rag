# utils/filters.py
# Helper functions to build ChromaDB metadata filter dicts.
# ChromaDB where-clause syntax is strict — these helpers prevent mistakes.
#
# Usage:
#   from utils.filters import by_department, by_year, combined
#
#   results = embedder.query(q, where=by_department("Monetary Policy"))
#   results = embedder.query(q, where=by_year(2023))
#   results = embedder.query(q, where=combined(dept="Payment Systems", year=2023))


def by_department(department: str) -> dict:
    """Filter by exact department name."""
    return {"department": {"$eq": department}}


def by_year(year: int) -> dict:
    """
    Filter circulars by year.
    Matches date strings containing the year e.g. '01/04/2023'.
    """
    return {"date": {"$contains": str(year)}}


def by_circular_no(circular_no: str) -> dict:
    """Filter by exact circular number."""
    return {"circular_no": {"$eq": circular_no}}


def combined(dept: str = None, year: int = None) -> dict | None:
    """
    Build a combined filter. Returns None if no filters specified.
    ChromaDB uses $and for multiple conditions.
    """
    conditions = []
    if dept:
        conditions.append({"department": {"$eq": dept}})
    if year:
        conditions.append({"date": {"$contains": str(year)}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}
