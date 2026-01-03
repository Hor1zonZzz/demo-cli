"""Local tracing for agent execution."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.tracing import TracingProcessor, Trace, Span

logger = logging.getLogger(__name__)


class LocalTracingProcessor(TracingProcessor):
    """Processor that logs traces locally to console and/or file.
    
    Provides visibility into agent execution without requiring
    OpenAI backend connectivity.
    """
    
    def __init__(
        self,
        log_to_console: bool = True,
        log_to_file: bool = False,
        log_dir: str = "data/traces",
        verbose: bool = False,
    ) -> None:
        """Initialize local tracing processor.
        
        Args:
            log_to_console: Print trace events to console.
            log_to_file: Save traces to JSON files.
            log_dir: Directory for trace files.
            verbose: Include detailed span data.
        """
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
            print(f"\n[TRACE] ▶ {trace.name} (id={trace.trace_id[:8]}...)")
    
    def on_trace_end(self, trace: Trace) -> None:
        """Called when a trace ends."""
        trace_data = self._current_traces.pop(trace.trace_id, None)
        if not trace_data:
            return
        
        trace_data["ended_at"] = datetime.now().isoformat()
        
        if self._log_to_console:
            span_count = len(trace_data["spans"])
            print(f"[TRACE] ◼ {trace.name} completed ({span_count} spans)")
        
        if self._log_to_file:
            self._save_trace(trace_data)
    
    def on_span_start(self, span: Span) -> None:
        """Called when a span starts."""
        if self._log_to_console and self._verbose:
            print(f"  [SPAN] ▶ {span.span_id[:8]}... {span.span_data.type}")
    
    def on_span_end(self, span: Span) -> None:
        """Called when a span ends."""
        trace_data = self._current_traces.get(span.trace_id)
        if not trace_data:
            return
        
        span_info = {
            "span_id": span.span_id,
            "type": span.span_data.type,
        }
        
        # Extract useful info based on span type
        span_data = span.span_data
        if hasattr(span_data, "name"):
            span_info["name"] = span_data.name
        if hasattr(span_data, "input"):
            span_info["input_preview"] = self._truncate(str(span_data.input), 200)
        if hasattr(span_data, "output"):
            span_info["output_preview"] = self._truncate(str(span_data.output), 200)
        
        trace_data["spans"].append(span_info)
        
        if self._log_to_console:
            type_str = span_data.type
            name_str = span_info.get("name", "")
            if name_str:
                print(f"  [SPAN] ◼ {type_str}: {name_str}")
            else:
                print(f"  [SPAN] ◼ {type_str}")
    
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
                print(f"  [TRACE] Saved to {filepath}")
        except Exception as e:
            logger.warning(f"Failed to save trace: {e}")


def setup_local_tracing(
    log_to_console: bool = True,
    log_to_file: bool = False,
    log_dir: str = "data/traces",
    verbose: bool = False,
) -> LocalTracingProcessor:
    """Setup local tracing and return the processor.
    
    Call this at app startup to enable local tracing.
    
    Args:
        log_to_console: Print trace events to console.
        log_to_file: Save traces to JSON files.
        log_dir: Directory for trace files.
        verbose: Include detailed span data.
    
    Returns:
        The configured LocalTracingProcessor.
    """
    from agents.tracing import set_trace_processors
    
    processor = LocalTracingProcessor(
        log_to_console=log_to_console,
        log_to_file=log_to_file,
        log_dir=log_dir,
        verbose=verbose,
    )
    
    # Replace default processors with our local one
    set_trace_processors([processor])
    
    return processor
