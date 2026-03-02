"""Configuration for Fellow Aiden brew settings."""

# Default brew profile name (must match a profile saved on your Aiden)
DEFAULT_PROFILE_NAME = "Default"

# Default water amount in ml (150-1500)
DEFAULT_WATER_AMOUNT = 500

# Minimum delay before brewing starts (in minutes)
# Note: The Aiden schedules based on when the brew ENDS, not starts.
# 6 minutes is the minimum buffer that works reliably.
MIN_DELAY_MINUTES = 6

# Additional buffer to account for brew duration (in minutes)
# This ensures the schedule time accounts for how long the brew takes
BREW_DURATION_BUFFER = 10
