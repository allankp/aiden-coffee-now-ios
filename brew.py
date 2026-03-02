#!/usr/bin/env python3
"""
Trigger a Fellow Aiden coffee maker to start brewing.

This script creates a temporary schedule to trigger a brew since the
Fellow Aiden API doesn't have a direct "brew now" command.
"""

import os
import sys
import time
from datetime import datetime, timedelta

from difflib import SequenceMatcher

from fellow_aiden import FellowAiden

from config import (
    BREW_DURATION_BUFFER,
    DEFAULT_PROFILE_NAME,
    DEFAULT_WATER_AMOUNT,
    MIN_DELAY_MINUTES,
)

# Minimum similarity score for fuzzy matching (0.0 - 1.0)
FUZZY_MATCH_THRESHOLD = 0.5


def get_credentials() -> tuple[str, str]:
    """Get Fellow credentials from environment variables."""
    email = os.environ.get("FELLOW_EMAIL")
    password = os.environ.get("FELLOW_PASSWORD")

    if not email or not password:
        print("Error: FELLOW_EMAIL and FELLOW_PASSWORD environment variables required")
        sys.exit(1)

    return email, password


def similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_matching_profiles(aiden: FellowAiden, profile_name: str) -> list[dict]:
    """
    Find all profiles that match the given name.
    
    Returns profiles that either:
    - Match exactly (case-insensitive)
    - Have similarity above threshold
    """
    profiles = aiden.get_profiles()
    matches = []
    
    for profile in profiles:
        title = profile.get("title", "")
        # Exact match (case-insensitive)
        if title.lower() == profile_name.lower():
            return [profile]  # Exact match, return immediately
        # Fuzzy match
        score = similarity(title, profile_name)
        if score >= FUZZY_MATCH_THRESHOLD:
            matches.append({"profile": profile, "score": score})
    
    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    return [m["profile"] for m in matches]


def find_profile_id(aiden: FellowAiden, profile_name: str) -> str | None:
    """
    Find a profile ID by name with fuzzy matching.
    
    - If exactly one match: returns the profile ID
    - If multiple matches: prints them and exits
    - If no matches: returns None
    """
    matches = find_matching_profiles(aiden, profile_name)
    
    if len(matches) == 1:
        profile = matches[0]
        print(f"Matched profile: {profile.get('title')} (id: {profile.get('id')})")
        return profile["id"]
    
    if len(matches) > 1:
        print(f"Error: Multiple profiles match '{profile_name}'")
        print("")
        print("Matching profiles:")
        for p in matches:
            score = similarity(p.get("title", ""), profile_name)
            print(f"  - {p.get('title', 'Unknown')} (id: {p.get('id')}, match: {score:.0%})")
        print("")
        print("Please use a more specific profile name.")
        
        # Write to GitHub summary if running in Actions
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a") as f:
                f.write("## ⚠️ Multiple Profiles Matched\n\n")
                f.write(f"Your search term `{profile_name}` matched multiple profiles:\n\n")
                f.write("| Profile | ID | Match |\n")
                f.write("|---------|-----|-------|\n")
                for p in matches:
                    score = similarity(p.get("title", ""), profile_name)
                    f.write(f"| {p.get('title', 'Unknown')} | {p.get('id')} | {score:.0%} |\n")
                f.write("\nPlease use a more specific profile name.\n")
        
        sys.exit(1)
    
    return None


def calculate_schedule_time(delay_minutes: int) -> tuple[str, list[bool]]:
    """
    Calculate the schedule time and days.

    The Aiden schedule time is when the brew ENDS, not starts.
    We need to add the brew duration buffer to get the right end time.

    Returns:
        Tuple of (time_string in HH:MM:SS format, days list for all days)
    """
    # Calculate target time (now + delay + brew duration)
    target_time = datetime.now() + timedelta(minutes=delay_minutes + BREW_DURATION_BUFFER)

    # Format as HH:MM:SS
    time_str = target_time.strftime("%H:%M:00")

    # Enable all days (we'll delete the schedule after it runs)
    days = [True, True, True, True, True, True, True]

    return time_str, days


def create_brew_schedule(
    aiden: FellowAiden,
    profile_name: str = DEFAULT_PROFILE_NAME,
    water_amount: int = DEFAULT_WATER_AMOUNT,
    delay_minutes: int = MIN_DELAY_MINUTES,
) -> str:
    """
    Create a temporary schedule to trigger a brew.

    Args:
        aiden: FellowAiden instance
        profile_name: Name of the brew profile to use
        water_amount: Amount of water in ml (150-1500)
        delay_minutes: Minutes to delay before brewing

    Returns:
        Schedule ID of the created schedule
    """
    # Find the profile
    profile_id = find_profile_id(aiden, profile_name)
    if not profile_id:
        profiles = aiden.get_profiles()
        print(f"Error: No profile matches '{profile_name}'")
        print("")
        print("Available profiles:")
        for p in profiles:
            print(f"  - {p.get('title', 'Unknown')} (id: {p.get('id')})")
        
        # Write to GitHub summary if running in Actions
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a") as f:
                f.write("## ❌ Profile Not Found\n\n")
                f.write(f"No profile matches `{profile_name}`.\n\n")
                f.write("### Available Profiles\n\n")
                f.write("| Profile | ID |\n")
                f.write("|---------|----|\n")
                for p in profiles:
                    f.write(f"| {p.get('title', 'Unknown')} | {p.get('id')} |\n")
        
        sys.exit(1)

    # Validate water amount
    water_amount = max(150, min(1500, water_amount))

    # Ensure minimum delay
    delay_minutes = max(MIN_DELAY_MINUTES, delay_minutes)

    # Calculate schedule time
    time_str, days = calculate_schedule_time(delay_minutes)

    # Create the schedule
    schedule = {
        "days": days,
        "secondFromStartOfTheDay": time_to_seconds(time_str),
        "enabled": True,
        "amountOfWater": water_amount,
        "profileId": profile_id,
    }

    print(f"Creating brew schedule:")
    print(f"  Profile: {profile_name} ({profile_id})")
    print(f"  Water: {water_amount}ml")
    print(f"  Scheduled end time: {time_str}")
    print(f"  (Brewing will start in approximately {delay_minutes} minutes)")

    result = aiden.create_schedule(schedule)

    # Get the schedule ID from the response or list schedules
    schedules = aiden.get_schedules()
    if schedules:
        # Return the most recent schedule ID
        return schedules[-1].get("id", "s0")

    return "s0"


def time_to_seconds(time_str: str) -> int:
    """Convert HH:MM:SS to seconds from midnight."""
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2]) if len(parts) > 2 else 0
    return hours * 3600 + minutes * 60 + seconds


def cleanup_schedule(aiden: FellowAiden, schedule_id: str, wait_minutes: int = 15):
    """
    Wait for brew to complete and clean up the temporary schedule.

    Args:
        aiden: FellowAiden instance
        schedule_id: ID of the schedule to delete
        wait_minutes: Minutes to wait before cleanup
    """
    print(f"Waiting {wait_minutes} minutes before cleanup...")
    time.sleep(wait_minutes * 60)

    print(f"Deleting temporary schedule {schedule_id}...")
    try:
        aiden.delete_schedule_by_id(schedule_id)
        print("Schedule cleaned up successfully")
    except Exception as e:
        print(f"Warning: Could not delete schedule: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Trigger Fellow Aiden to brew coffee")
    parser.add_argument(
        "--profile",
        "-p",
        default=DEFAULT_PROFILE_NAME,
        help=f"Brew profile name (default: {DEFAULT_PROFILE_NAME})",
    )
    parser.add_argument(
        "--water",
        "-w",
        type=int,
        default=DEFAULT_WATER_AMOUNT,
        help=f"Water amount in ml (default: {DEFAULT_WATER_AMOUNT})",
    )
    parser.add_argument(
        "--delay",
        "-d",
        type=int,
        default=MIN_DELAY_MINUTES,
        help=f"Delay in minutes (default: {MIN_DELAY_MINUTES})",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't wait and cleanup the schedule (useful for CI)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit",
    )

    args = parser.parse_args()

    # Get credentials and connect
    email, password = get_credentials()
    print(f"Connecting to Fellow Aiden as {email}...")

    aiden = FellowAiden(email, password)

    # Get brewer name
    name = aiden.get_display_name()
    print(f"Connected to: {name}")

    # List profiles mode
    if args.list_profiles:
        print("\nAvailable profiles:")
        for p in aiden.get_profiles():
            print(f"  - {p.get('title', 'Unknown')} (id: {p.get('id')})")
        return

    # Create the brew schedule
    schedule_id = create_brew_schedule(
        aiden,
        profile_name=args.profile,
        water_amount=args.water,
        delay_minutes=args.delay,
    )

    print(f"\n☕ Brew scheduled! Your coffee will be ready soon.")

    # Cleanup if not disabled
    if not args.no_cleanup:
        cleanup_schedule(aiden, schedule_id)
    else:
        print(f"Note: Remember to manually delete schedule {schedule_id} later")


if __name__ == "__main__":
    main()
