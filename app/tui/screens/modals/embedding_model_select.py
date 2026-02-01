"""Embedding model selection modal screen."""

from pathlib import Path
from typing import Optional, List, Dict, Any

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Static, OptionList, Footer
from textual.widgets.option_list import Option
from textual.screen import ModalScreen
from textual import on, work
from textual.binding import Binding
from textual.worker import Worker, WorkerState

# Import model definitions from shared module
from app.models.embedding_models import EMBEDDING_MODELS, get_model_by_id, get_model_dimensions


def is_model_cached(model_id: str) -> bool:
    """Check if a model is already downloaded and cached.
    
    Args:
        model_id: The model identifier
        
    Returns:
        True if model is cached, False otherwise
    """
    try:
        from app.search.model_downloader import is_model_cached as check_cached
        return check_cached(model_id)
    except ImportError:
        # Fallback: check both cache locations manually
        import os
        
        # Check sentence-transformers cache
        st_cache = os.environ.get(
            "SENTENCE_TRANSFORMERS_HOME",
            str(Path.home() / ".cache" / "torch" / "sentence_transformers")
        )
        st_model_path = Path(st_cache) / f"sentence-transformers_{model_id}"
        if st_model_path.exists() and (st_model_path / "config.json").exists():
            return True
        
        # Check HuggingFace hub cache
        hf_cache = os.environ.get("HF_HOME")
        if hf_cache:
            hf_hub = Path(hf_cache) / "hub"
        else:
            hf_hub = Path.home() / ".cache" / "huggingface" / "hub"
        
        hf_model_path = hf_hub / f"models--sentence-transformers--{model_id}"
        if hf_model_path.exists():
            snapshots = hf_model_path / "snapshots"
            if snapshots.exists() and any(snapshots.iterdir()):
                return True
        
        return False


class EmbeddingModelSelectScreen(ModalScreen[Optional[str]]):
    """Modal screen for selecting embedding model."""

    CSS = """
    EmbeddingModelSelectScreen {
        align: center middle;
    }

    #dialog {
        width: 95;
        height: 30;
        border: double $primary;
        background: $surface;
        padding: 1;
    }

    #title {
        height: auto;
        text-style: bold;
        color: $primary;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #model-content {
        height: 1fr;
    }

    #model-list-container {
        width: 32;
        height: 100%;
        border: heavy $primary;
        padding: 0 1;
        background: $panel;
    }

    #model-list {
        height: 100%;
        background: $panel;
    }

    #details-container {
        width: 1fr;
        height: 100%;
        border: heavy $secondary;
        padding: 1;
        margin-left: 1;
        background: $panel;
    }

    #details-title {
        height: auto;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    #model-id {
        height: auto;
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }

    .specs-row {
        height: auto;
        margin-bottom: 0;
    }

    .spec-label {
        width: 14;
        color: $text-muted;
    }

    .spec-value {
        color: $text;
    }

    #cache-status {
        height: auto;
        margin-top: 1;
        padding: 0 1;
    }

    #cache-status.cached {
        color: $success;
    }

    #cache-status.not-cached {
        color: $warning;
    }

    #cache-status.downloading {
        color: $primary;
    }

    #model-description {
        height: auto;
        color: $secondary;
        margin-top: 1;
        margin-bottom: 1;
    }

    #recommended-for {
        height: auto;
        color: $success;
        text-style: italic;
    }

    #warning-container {
        height: auto;
        margin-top: 1;
        padding: 1;
        background: $warning 20%;
        border: solid $warning;
    }

    #warning-text {
        height: auto;
        color: $warning;
    }

    #dimension-warning {
        height: auto;
        color: $error;
        text-style: bold;
        margin-top: 1;
    }

    #buttons {
        height: auto;
        margin-top: 1;
    }

    Button {
        height: auto;
        min-width: 12;
    }

    Button.-primary {
        color: $background;
        background: $primary;
        text-style: bold;
    }

    Button.-default {
        color: $text;
        background: $surface;
        border: tall $primary;
    }

    Button.-success {
        color: $background;
        background: $success;
        text-style: bold;
    }

    Button:focus {
        text-style: bold reverse;
    }

    Button:disabled {
        opacity: 0.5;
    }

    OptionList:focus {
        border: tall $accent;
    }

    OptionList > .option-list--option-highlighted {
        background: $primary;
        color: $text;
        text-style: bold;
    }

    Footer {
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("up,k", "cursor_up", "Up", show=False),
        Binding("down,j", "cursor_down", "Down", show=False),
        Binding("enter,ctrl+s", "select_model", "Apply"),
        Binding("d", "download_model", "Download"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current_model: str):
        """Initialize with current model.
        
        Args:
            current_model: Currently selected model ID
        """
        super().__init__()
        self.current_model = current_model
        self.selected_model = current_model
        self.current_dimensions = get_model_dimensions(current_model)
        self.downloading = False
        self._mounted = False

    def compose(self) -> ComposeResult:
        """Compose the model selection dialog."""
        with Vertical(id="dialog"):
            yield Label("[ SELECT EMBEDDING MODEL ]", id="title")

            with Horizontal(id="model-content"):
                # Model list on the left
                with Container(id="model-list-container"):
                    yield OptionList(
                        *[Option(model["name"], id=model["id"]) for model in EMBEDDING_MODELS],
                        id="model-list"
                    )

                # Details panel on the right
                with Vertical(id="details-container"):
                    yield Label("", id="details-title")
                    yield Label("", id="model-id")
                    
                    # Specs
                    with Horizontal(classes="specs-row"):
                        yield Label("Dimensions:", classes="spec-label")
                        yield Label("", classes="spec-value", id="spec-dimensions")
                    
                    with Horizontal(classes="specs-row"):
                        yield Label("Model Size:", classes="spec-label")
                        yield Label("", classes="spec-value", id="spec-size")
                    
                    with Horizontal(classes="specs-row"):
                        yield Label("RAM Usage:", classes="spec-label")
                        yield Label("", classes="spec-value", id="spec-ram")
                    
                    with Horizontal(classes="specs-row"):
                        yield Label("Speed:", classes="spec-label")
                        yield Label("", classes="spec-value", id="spec-speed")
                    
                    with Horizontal(classes="specs-row"):
                        yield Label("Quality:", classes="spec-label")
                        yield Label("", classes="spec-value", id="spec-quality")
                    
                    # Cache status
                    yield Label("", id="cache-status")
                    
                    yield Label("", id="model-description")
                    yield Label("", id="recommended-for")
                    yield Label("", id="dimension-warning")

            # Warning banner
            with Container(id="warning-container"):
                yield Label(
                    "⚠ Changing models requires restart. Press 'd' to download model first.",
                    id="warning-text"
                )

            with Horizontal(id="buttons", classes="modal-buttons"):
                yield Button("Download", variant="default", id="download")
                yield Button("Apply", variant="primary", id="apply")
                yield Button("Cancel", variant="default", id="cancel")
        yield Footer()

    def on_mount(self) -> None:
        """Set up initial selection."""
        option_list = self.query_one("#model-list", OptionList)
        option_list.focus()

        # Find and highlight current model
        for i, model in enumerate(EMBEDDING_MODELS):
            if model["id"] == self.current_model:
                option_list.highlighted = i
                break
        else:
            # Current model not in list, select first
            option_list.highlighted = 0

        # Mark as mounted and update details
        self._mounted = True
        self._update_details(self.current_model)

    def _format_speed(self, speed: int) -> str:
        """Format speed rating as visual indicator."""
        return "⚡" * speed + "  " * (3 - speed) + ["Slow", "Medium", "Fast"][speed - 1]

    def _format_quality(self, quality: int) -> str:
        """Format quality rating as visual indicator."""
        filled = "★" * quality
        empty = "☆" * (5 - quality)
        labels = ["", "Basic", "Fair", "Good", "Great", "Excellent"]
        return f"{filled}{empty} {labels[quality]}"

    def _update_details(self, model_id: str) -> None:
        """Update the details panel for a model."""
        try:
            model = get_model_by_id(model_id)
            
            if not model:
                # Model not in our list (custom model in .env)
                self.query_one("#details-title", Label).update(model_id)
                self.query_one("#model-id", Label).update("(Custom model)")
                self.query_one("#spec-dimensions", Label).update("Unknown")
                self.query_one("#spec-size", Label).update("Unknown")
                self.query_one("#spec-ram", Label).update("Unknown")
                self.query_one("#spec-speed", Label).update("Unknown")
                self.query_one("#spec-quality", Label).update("Unknown")
                self._update_cache_status(model_id)
                self.query_one("#model-description", Label).update("")
                self.query_one("#recommended-for", Label).update("")
                self.query_one("#dimension-warning", Label).update("")
                return

            # Update all fields
            self.query_one("#details-title", Label).update(model["name"])
            self.query_one("#model-id", Label).update(f"ID: {model['id']}")
            self.query_one("#spec-dimensions", Label).update(str(model["dimensions"]))
            self.query_one("#spec-size", Label).update(f"~{model['size_mb']} MB")
            self.query_one("#spec-ram", Label).update(f"~{model['ram_mb']} MB")
            self.query_one("#spec-speed", Label).update(self._format_speed(model["speed"]))
            self.query_one("#spec-quality", Label).update(self._format_quality(model["quality"]))
            
            # Update cache status
            self._update_cache_status(model_id)
            
            self.query_one("#model-description", Label).update(model["description"])
            self.query_one("#recommended-for", Label).update(f"Best for: {model['recommended_for']}")

            # Check for dimension mismatch warning
            warning_label = self.query_one("#dimension-warning", Label)
            if (self.current_dimensions is not None and 
                model["dimensions"] != self.current_dimensions):
                warning_label.update(
                    f"⚠ Dimension change: {self.current_dimensions} → {model['dimensions']}\n"
                    "Existing embeddings may become incompatible!"
                )
            else:
                warning_label.update("")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error updating details for {model_id}: {e}")

    def _update_cache_status(self, model_id: str) -> None:
        """Update cache status display for a model."""
        try:
            cache_label = self.query_one("#cache-status", Label)
            download_btn = self.query_one("#download", Button)
        except Exception:
            return  # Widgets not ready yet
        
        if self.downloading:
            cache_label.update("⏳ Downloading...")
            download_btn.disabled = True
            download_btn.label = "Downloading..."
        elif is_model_cached(model_id):
            cache_label.update("✓ Downloaded & Ready")
            download_btn.disabled = False
            download_btn.label = "Re-download"
        else:
            cache_label.update("✗ Not downloaded")
            download_btn.disabled = False
            download_btn.label = "Download"

    @on(OptionList.OptionHighlighted, "#model-list")
    def on_model_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Update details when model is highlighted."""
        if not self._mounted:
            return
        if event.option and event.option.id:
            self.selected_model = str(event.option.id)
            self._update_details(self.selected_model)

    def action_cursor_up(self) -> None:
        """Move cursor up in model list."""
        self.query_one("#model-list", OptionList).action_cursor_up()

    def action_cursor_down(self) -> None:
        """Move cursor down in model list."""
        self.query_one("#model-list", OptionList).action_cursor_down()

    def action_select_model(self) -> None:
        """Apply the currently highlighted model."""
        self.dismiss(self.selected_model)

    def action_download_model(self) -> None:
        """Download the currently selected model."""
        if not self.downloading:
            self._start_download(self.selected_model)

    @on(Button.Pressed, "#download")
    def handle_download(self) -> None:
        """Handle download button press."""
        if not self.downloading:
            self._start_download(self.selected_model)

    def _start_download(self, model_id: str) -> None:
        """Start downloading a model."""
        self.downloading = True
        self._update_cache_status(model_id)
        self.app.notify(f"Downloading {model_id}...\nThis may take a few minutes.", timeout=5)
        self._download_model_worker(model_id)

    @work(thread=True, name="download_model")
    def _download_model_worker(self, model_id: str) -> bool:
        """Background worker to download model."""
        try:
            from app.search.model_downloader import download_model
            success = download_model(model_id, force=True)
            return success
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Download failed for {model_id}: {e}")
            raise  # Re-raise so worker captures the error

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes."""
        # Only handle our download worker
        if event.worker.name != "download_model":
            return
            
        if event.state == WorkerState.SUCCESS:
            self.downloading = False
            self._update_cache_status(self.selected_model)
            try:
                if event.worker.result:
                    self.app.notify("✓ Model downloaded successfully!", severity="information")
                else:
                    self.app.notify("✗ Download failed. Check logs for details.", severity="error")
            except Exception:
                self.app.notify("✓ Download complete!", severity="information")
        elif event.state in (WorkerState.ERROR, WorkerState.CANCELLED):
            self.downloading = False
            self._update_cache_status(self.selected_model)
            try:
                error_msg = str(event.worker.error) if event.worker.error else "Unknown error"
                self.app.notify(f"✗ Download failed: {error_msg}", severity="error")
            except Exception:
                self.app.notify("✗ Download failed", severity="error")

    @on(Button.Pressed, "#apply")
    def handle_apply(self) -> None:
        """Handle apply button press."""
        self.dismiss(self.selected_model)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle escape key."""
        self.handle_cancel()
