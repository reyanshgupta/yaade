"""Custom themes for Yaade TUI application."""

from textual.theme import Theme


# Cyberpunk theme - Neon pink/magenta + cyan aesthetic
cyberpunk_theme = Theme(
    name="cyberpunk",
    primary="#ff00ff",       # Hot magenta/pink - primary neon
    secondary="#00ffff",     # Electric cyan - secondary neon
    accent="#ff1493",        # Deep pink for accents
    foreground="#e0e0ff",    # Light blue-tinted text
    background="#0a0a12",    # Very dark blue-black
    surface="#12121a",       # Dark surface with blue tint
    panel="#1a1a2e",         # Slightly lighter panel
    success="#00ff9f",       # Neon green
    warning="#ffff00",       # Neon yellow
    error="#ff0040",         # Neon red
    dark=True,
    variables={
        "block-cursor-text-style": "bold reverse",
        "block-cursor-foreground": "#ff00ff",
        "block-cursor-background": "#00ffff",
        "footer-key-foreground": "#00ffff",
        "footer-description-foreground": "#ff00ff",
        "footer-background": "#0a0a12",
        "input-cursor-foreground": "#ff00ff",
        "input-cursor-background": "#00ffff",
        "input-selection-background": "#ff00ff 35%",
        "scrollbar-color": "#ff00ff",
        "scrollbar-color-hover": "#00ffff",
        "scrollbar-background": "#1a1a2e",
        # Button text colors - ensure high contrast
        "button-foreground": "#e0e0ff",
        "button-color-foreground": "#0a0a12",  # Dark text on bright primary/success/etc backgrounds
    },
)

# Cyberpunk variant - More subdued for extended use
cyberpunk_soft_theme = Theme(
    name="cyberpunk-soft",
    primary="#c850c0",       # Softer magenta
    secondary="#4fc3dc",     # Softer cyan
    accent="#ff6b9d",        # Soft pink accent
    foreground="#d0d0e0",    # Soft light text
    background="#0d0d14",    # Dark background
    surface="#14141e",       # Dark surface
    panel="#1c1c2a",         # Panel color
    success="#50c878",       # Softer green
    warning="#f0c040",       # Softer yellow
    error="#e04060",         # Softer red
    dark=True,
    variables={
        "block-cursor-text-style": "bold",
        "footer-key-foreground": "#4fc3dc",
        "footer-description-foreground": "#c850c0",
        "input-selection-background": "#c850c0 30%",
        "scrollbar-color": "#c850c0",
        "scrollbar-color-hover": "#4fc3dc",
        # Button text colors - ensure high contrast
        "button-foreground": "#d0d0e0",
        "button-color-foreground": "#0d0d14",  # Dark text on bright primary/success/etc backgrounds
    },
)

# Neon Nights - Alternative cyberpunk with purple focus
neon_nights_theme = Theme(
    name="neon-nights",
    primary="#9d4edd",       # Vivid purple
    secondary="#00f5d4",     # Bright teal
    accent="#f72585",        # Hot pink
    foreground="#e0e0e8",    # Light text
    background="#0f0f1a",    # Dark purple-black
    surface="#1a1a28",       # Dark surface
    panel="#242436",         # Panel
    success="#00f5a0",       # Neon mint
    warning="#fee440",       # Bright yellow
    error="#ff006e",         # Neon pink-red
    dark=True,
    variables={
        "footer-key-foreground": "#00f5d4",
        "footer-description-foreground": "#9d4edd",
        "input-selection-background": "#9d4edd 35%",
        "scrollbar-color": "#9d4edd",
        "scrollbar-color-hover": "#00f5d4",
        # Button text colors - ensure high contrast
        "button-foreground": "#e0e0e8",
        "button-color-foreground": "#0f0f1a",  # Dark text on bright primary/success/etc backgrounds
    },
)

# List of all custom themes for easy registration
CUSTOM_THEMES = [
    cyberpunk_theme,
    cyberpunk_soft_theme,
    neon_nights_theme,
]
