"""Test-session setup: run the API offline (no live market/news calls) so tests are fast and deterministic."""

import os

os.environ["LIVE_MARKET_DATA"] = "false"
