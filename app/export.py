# app/export.py
# Utility functions for exporting chat history from Streamlit session.

import json
from datetime import datetime


def chat_to_text(messages: list) -> str:
    """Convert session messages to plain text transcript."""
    lines = [f"RBI Circular Assistant — Chat Export", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "=" * 60, ""]
    for msg in messages:
        role = "You" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}:")
        lines.append(msg["content"])
        if msg.get("sources"):
            lines.append("Sources:")
            for s in msg["sources"]:
                lines.append(f"  - {s.get('circular_no','N/A')} ({s.get('date','N/A')})")
        lines.append("")
    return "\n".join(lines)


def chat_to_json(messages: list) -> str:
    """Convert session messages to JSON string."""
    export = {
        "exported_at": datetime.now().isoformat(),
        "messages": messages
    }
    return json.dumps(export, indent=2, default=str)
