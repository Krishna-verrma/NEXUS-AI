import csv
import json
from pathlib import Path
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.tools.filesystem import _resolve_safe_path

class ParseDocumentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="documents:parse_document",
            description="Parses structured and unstructured documents (CSV, JSON, Markdown, TXT).",
            permission_level=PermissionLevel.READ_ONLY,
            input_schema={"path": "string (file path to document)"},
            output_schema={
                "file_type": "string",
                "row_count": "integer (for tabular)",
                "columns": "list of str (for tabular)",
                "data": "any parsed structure",
                "summary": "string"
            }
        )

    async def execute(self, path: Optional[str] = None, file_path: Optional[str] = None, include_statistics: bool = False, **kwargs: Any) -> ToolResult:
        try:
            target_str = path or file_path or kwargs.get("path") or kwargs.get("file_path")
            if not target_str:
                return ToolResult(success=False, error="No file path provided to documents:parse_document.")
            safe_p = _resolve_safe_path(target_str)
            if not safe_p.exists():
                return ToolResult(success=False, error=f"Document '{target_str}' does not exist.")

            ext = safe_p.suffix.lower()

            if ext == ".csv":
                with open(safe_p, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    fieldnames = reader.fieldnames or []

                statistics = {}
                trend_timeline = []
                anomalies = []
                for field in fieldnames:
                    vals = []
                    for r in rows:
                        try:
                            v_clean = str(r.get(field, "")).replace("$", "").replace(",", "").strip()
                            vals.append(float(v_clean))
                        except Exception:
                            pass
                    if vals:
                        tot = sum(vals)
                        avg = tot / len(vals)
                        mn = min(vals)
                        mx = max(vals)
                        statistics[field] = {
                            "total": tot,
                            "mean": round(avg, 2),
                            "min": mn,
                            "max": mx,
                            "count": len(vals)
                        }

                # Build trend timeline if date column exists
                for r in rows:
                    dt_val = r.get("Date") or r.get("date") or r.get("Month") or r.get("Period")
                    rev_val = r.get("Revenue") or r.get("revenue") or r.get("Amount")
                    if dt_val:
                        trend_timeline.append({"period": dt_val, "value": rev_val})

                return ToolResult(
                    success=True,
                    data={
                        "file_type": "csv",
                        "row_count": len(rows),
                        "columns": fieldnames,
                        "sample_rows": rows[:5],
                        "rows": rows,
                        "statistics": statistics,
                        "trend_timeline": trend_timeline,
                        "anomalies": anomalies
                    }
                )

            elif ext == ".json":
                with open(safe_p, "r", encoding="utf-8", errors="replace") as f:
                    loaded = json.load(f)
                return ToolResult(
                    success=True,
                    data={
                        "file_type": "json",
                        "is_list": isinstance(loaded, list),
                        "item_count": len(loaded) if isinstance(loaded, list) else 1,
                        "data": loaded
                    }
                )

            elif ext in (".md", ".txt"):
                content = safe_p.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                return ToolResult(
                    success=True,
                    data={
                        "file_type": ext.lstrip("."),
                        "line_count": len(lines),
                        "char_count": len(content),
                        "content": content
                    }
                )

            else:
                content = safe_p.read_text(encoding="utf-8", errors="ignore")
                return ToolResult(
                    success=True,
                    data={
                        "file_type": "text",
                        "char_count": len(content),
                        "content": content[:5000]
                    }
                )

        except Exception as e:
            return ToolResult(success=False, error=str(e))
