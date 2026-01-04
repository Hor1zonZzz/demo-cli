"""Local tracing for agent execution."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

from agents.tracing import TracingProcessor, Trace, Span

logger = logging.getLogger(__name__)


class LocalTracingProcessor(TracingProcessor):
    """Processor that logs traces locally to console and/or file.
    
    Provides visibility into agent execution without requiring
    OpenAI backend connectivity.
    """
    
    def __init__(
        self,
        console: Console | None = None,
        log_to_console: bool = True,
        log_to_file: bool = False,
        log_dir: str = "data/traces",
        verbose: bool = False,
    ) -> None:
        """Initialize local tracing processor.
        
        Args:
            console: Rich Console for output (avoids spinner conflicts).
            log_to_console: Print trace events to console.
            log_to_file: Save traces to JSON files.
            log_dir: Directory for trace files.
            verbose: Include detailed span data.
        """
        self._console = console or Console()
        self._log_to_console = log_to_console
        self._log_to_file = log_to_file
        self._log_dir = Path(log_dir)
        self._verbose = verbose
        self._current_traces: dict[str, dict] = {}
        
        if log_to_file:
            self._log_dir.mkdir(parents=True, exist_ok=True)
    
    def on_trace_start(self, trace: Trace) -> None:
        """Called when a trace starts."""
        trace_data = {
            "trace_id": trace.trace_id,
            "name": trace.name,
            "started_at": datetime.now().isoformat(),
            "spans": [],
        }
        self._current_traces[trace.trace_id] = trace_data
        
        if self._log_to_console:
            self._console.print(f"\n[dim][TRACE] ▶ {trace.name} (id={trace.trace_id[:8]}...)[/dim]")
    
    def on_trace_end(self, trace: Trace) -> None:
        """Called when a trace ends."""
        trace_data = self._current_traces.pop(trace.trace_id, None)
        if not trace_data:
            return
        
        trace_data["ended_at"] = datetime.now().isoformat()
        
        if self._log_to_console:
            span_count = len(trace_data["spans"])
            self._console.print(f"[dim][TRACE] ◼ {trace.name} completed ({span_count} spans)[/dim]")
        
        if self._log_to_file:
            self._save_trace(trace_data)
    
    def on_span_start(self, span: Span) -> None:
        """Called when a span starts."""
        if self._log_to_console and self._verbose:
            self._console.print(f"[dim]  [SPAN] ▶ {span.span_id[:8]}... {span.span_data.type}[/dim]")
    
    def on_span_end(self, span: Span) -> None:
        """Called when a span ends."""
        trace_data = self._current_traces.get(span.trace_id)
        if not trace_data:
            return
        
        # Get full exported data from the SDK
        span_export = span.export()
        if not span_export:
            return

        # Extract core info and the complete span_data
        span_info = {
            "span_id": span_export.get("id"),
            "parent_id": span_export.get("parent_id"),
            "started_at": span_export.get("started_at"),
            "ended_at": span_export.get("ended_at"),
            "error": span_export.get("error"),
        }
        
        # Merge all data from span_data (contains full input/output)
        inner_data = span_export.get("span_data", {})
        span_info.update(inner_data)
        
        # Add previews only for console-friendly quick view in the JSON if desired, 
        # but the keys above now contain the FULL content.
        if "input" in inner_data:
            span_info["input_preview"] = self._truncate(str(inner_data["input"]), 200)
        if "output" in inner_data:
            span_info["output_preview"] = self._truncate(str(inner_data["output"]), 200)
        
        trace_data["spans"].append(span_info)
        
        if self._log_to_console:
            type_str = inner_data.get("type", "unknown")
            name_str = inner_data.get("name", "")
            if name_str:
                self._console.print(f"[dim]  [SPAN] ◼ {type_str}: {name_str}[/dim]")
            else:
                self._console.print(f"[dim]  [SPAN] ◼ {type_str}[/dim]")
    
    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text for logging."""
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."
    
    def _save_trace(self, trace_data: dict) -> None:
        """Save trace to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{timestamp}_{trace_data['trace_id'][:8]}.json"
        filepath = self._log_dir / filename
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(trace_data, f, ensure_ascii=False, indent=2)
            if self._verbose:
                self._console.print(f"[dim]  [TRACE] Saved to {filepath}[/dim]")
        except Exception as e:
            logger.warning(f"Failed to save trace: {e}")

    def force_flush(self) -> None:
        """Force flush any pending traces.
        
        For local tracing, traces are written synchronously,
        so this is a no-op.
        """
        pass

    def shutdown(self) -> None:
        """Shutdown the processor.
        
        Clears any pending traces.
        """
        self._current_traces.clear()


def setup_local_tracing(
    console: Console | None = None,
    log_to_console: bool = True,
    log_to_file: bool = False,
    log_dir: str = "data/traces",
    verbose: bool = False,
) -> LocalTracingProcessor:
    """Setup local tracing and return the processor.
    
    Call this at app startup to enable local tracing.
    
    Args:
        console: Rich Console for output (recommended to pass app's console).
        log_to_console: Print trace events to console.
        log_to_file: Save traces to JSON files.
        log_dir: Directory for trace files.
        verbose: Include detailed span data.
    
    Returns:
        The configured LocalTracingProcessor.
    """
    from agents.tracing import set_trace_processors
    
    processor = LocalTracingProcessor(
        console=console,
        log_to_console=log_to_console,
        log_to_file=log_to_file,
        log_dir=log_dir,
        verbose=verbose,
    )
    
    # Replace default processor with our local one to prevent cloud export errors
    set_trace_processors([processor])
    
    return processor
