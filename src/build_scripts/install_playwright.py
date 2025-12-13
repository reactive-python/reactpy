# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import subprocess

print("Installing Playwright browsers...")  # noqa: T201

# Install Chromium browser for Playwright, and fail if it cannot be installed
subprocess.run(["playwright", "install", "chromium"], check=True)  # noqa: S607

# Try to install system dependencies. We don't generate an exception if this fails
# as *nix systems (such as WSL) return a failure code if there are *any* dependencies
# that could be cleaned up via `sudo apt autoremove`. This occurs even if we weren't
# the ones to install those dependencies in the first place.
subprocess.run(["playwright", "install-deps"], check=False)  # noqa: S607
