"""
Supabase Client Helper for Ticker Search
"""

import streamlit as st
from supabase import create_client, Client
from config.settings import settings
import pandas as pd
from datetime import datetime, timedelta


# Cache the supabase client connection
@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    try:
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_KEY
        if not url or not key:
            # Fallback to st.secrets if available, though settings should handle it
            return None
        return create_client(url, key)
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return None


# Cache the ticker data to avoid too many DB calls
# Refresh every hour (ttl=3600)
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_tickers():
    """Fetch all tickers from Supabase for local searching"""
    client = get_supabase_client()
    if not client:
        return []

    try:
        # Fetch only necessary columns
        response = (
            client.table("tickers").select("ticker, korean_name, keywords").execute()
        )
        data = response.data
        return data
    except Exception as e:
        print(f"Error fetching tickers: {e}")
        return []


@st.cache_data(ttl=60, show_spinner=False)
def search_tickers(search_term: str):
    """
    Search tickers by term.

    Args:
        search_term (str): User input string

    Returns:
        list: List of tuples (display_string, value_string) for streamlit-searchbox
    """
    if not search_term:
        return []

    search_term = search_term.lower().strip()
    all_tickers = fetch_all_tickers()

    results = []

    for item in all_tickers:
        ticker = item.get("ticker", "").upper()
        korean_name = item.get("korean_name", "") or ""
        keywords = item.get("keywords", []) or []

        # Ensure keywords is a list (handle potential None or non-list)
        if hasattr(keywords, "tolist"):  # If numpy array
            keywords = keywords.tolist()
        if not isinstance(keywords, list):
            keywords = []

        # Add ticker and korean name to search targets
        search_targets = [ticker.lower(), korean_name.lower()] + [
            k.lower() for k in keywords
        ]

        # Check if search term is in any of the targets
        # logic: partial match for any field
        matched = False
        for target in search_targets:
            if search_term in target:
                matched = True
                break

        if matched:
            # Format: "**AAPL** | 애플"
            display_text = f"**{ticker}** | {korean_name}"
            results.append((display_text, ticker))

    # Sort results: shorter matches first (usually more relevant), then alphabetical
    # But prioritize starting with the search term

    def sort_key(item):
        display, val = item
        # extracting pure text might be complex, simplified sort:
        return len(display)

    results.sort(key=sort_key)

    # [NEW] Add the raw search term as a "Direct Input" option at the top
    # This allows users to select "Hearthstone" even if it's not in the DB
    if search_term:
        direct_input_display = f"🔍 직접 입력: {search_term}"
        # Prevent duplicates if exact match exists but ensure manual option is always available
        results.insert(0, (direct_input_display, search_term))

    return results
