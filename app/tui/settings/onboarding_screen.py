"""Minimal first-run onboarding screen."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Center
from textual.widgets import Label, Button, Footer
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding

from ..screens.modals import StorageConfigScreen


class OnboardingScreen(ModalScreen[bool]):
    """Minimal first-run: welcome, optional storage, get started."""

    CSS_PATH = [
        Path(__file__).parent.parent / "styles" / "settings.tcss",
    ]

    CSS = """
    OnboardingScreen {
        align: center middle;
    }

    #onboarding-dialog {
        width: 52;
        border: double $primary;
        background: $surface;
        padding: 2;
    }

    #onboarding-title {
        text-align: center;
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }

    #onboarding-blurb {
        text-align: center;
        color: $secondary;
        margin-bottom: 2;
        padding: 0 1;
    }

    #onboarding-buttons {
        height: auto;
        padding-top: 1;
    }

    OnboardingScreen Button {
        width: 100%;
        margin-bottom: 1;
    }

    OnboardingScreen Button.-primary {
        margin-bottom: 0;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Quit"),
        Binding("enter", "get_started", "Get started", show=False),
    ]

    def __init__(self, config_data: dict):
        super().__init__()
        self.config_data = config_data

    def compose(self) -> ComposeResult:
        data_dir = self.config_data.get("data_dir", "~/.yaade")
        with Center():
            with Vertical(id="onboarding-dialog"):
                yield Label("Welcome to Yaade", id="onboarding-title")
                yield Label(
                    f"Memories will be stored in {data_dir}. You can change this in Settings later.",
                    id="onboarding-blurb",
                )
                with Vertical(id="onboarding-buttons"):
                    yield Button("Change location", id="change_storage", variant="default")
                    yield Button("Get started", id="get_started", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#get_started", Button).focus()

    @on(Button.Pressed, "#change_storage")
    async def handle_change_storage(self) -> None:
        current = self.config_data.get("data_dir", "~/.yaade")

        def callback(new_path: Optional[str]) -> None:
            if new_path is not None:
                from ..utils import ConfigManager
                if ConfigManager.update_env_variable("YAADE_DATA_DIR", new_path):
                    self.config_data["data_dir"] = new_path
                    self.app.notify(f"Storage set to {new_path}", severity="information")
                    # Refresh blurb
                    blurb = self.query_one("#onboarding-blurb", Label)
                    blurb.update(
                        f"Memories will be stored in {new_path}. You can change this in Settings later."
                    )

        await self.app.push_screen(StorageConfigScreen(current), callback)

    @on(Button.Pressed, "#get_started")
    def handle_get_started(self) -> None:
        self.dismiss(True)

    def action_get_started(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.app.exit()
