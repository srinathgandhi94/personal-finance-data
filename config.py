"""
Load configuration from environment variables.
Reads from .env file (gitignored) using python-dotenv.
Create a .env file in the project root with your actual values.
"""

import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Validate and load required environment variables
DATABASE_URL: str = os.environ.get("DATABASE_URL") or ""
GOOGLE_CREDENTIALS_PATH: str = os.environ.get("GOOGLE_CREDENTIALS_PATH") or ""
GOOGLE_SHEET_ID_PORTFOLIO: str = os.environ.get("GOOGLE_SHEET_ID_PORTFOLIO") or ""
GOOGLE_SHEET_ID_INVESTMENT_REPORT: str = os.environ.get("GOOGLE_SHEET_ID_INVESTMENT_REPORT") or ""

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. Set it in .env file."
    )
if not GOOGLE_CREDENTIALS_PATH:
    raise ValueError(
        "GOOGLE_CREDENTIALS_PATH environment variable is required. Set it in .env file."
    )
if not GOOGLE_SHEET_ID_PORTFOLIO:
    raise ValueError(
        "GOOGLE_SHEET_ID_PORTFOLIO environment variable is required. Set it in .env file."
    )
if not GOOGLE_SHEET_ID_INVESTMENT_REPORT:
    raise ValueError(
        "GOOGLE_SHEET_ID_INVESTMENT_REPORT environment variable is required. Set it in .env file."
    )

# Normalize path for Windows
if "/" in GOOGLE_CREDENTIALS_PATH:
    GOOGLE_CREDENTIALS_PATH = GOOGLE_CREDENTIALS_PATH.replace("/", os.sep)
