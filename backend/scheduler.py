#!/usr/bin/env python3
"""
Daily Scheduler for AI Agents
Runs agents at specified time each day
"""

import schedule
import time
import subprocess
import sys
from datetime import datetime

def run_agents_job():
    """Execute the agents script"""
    print(f"\n{'='*50}")
    print(f"Running AI Agents at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    try:
        # Run agents.py
        result = subprocess.run(
            [sys.executable, "agents.py", "1"],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        if result.returncode == 0:
            print("\n✓ Agents completed successfully")
        else:
            print(f"\n✖ Agents failed with exit code {result.returncode}")

    except Exception as e:
        print(f"✖ Error running agents: {e}")

def main():
    """Main scheduler loop"""
    print("╔════════════════════════════════════╗")
    print("║   AI AGENTS SCHEDULER              ║")
    print("║   Running daily at 09:00           ║")
    print("╚════════════════════════════════════╝")
    print("")

    # Schedule daily run at 9:00 AM
    schedule.every().day.at("09:00").do(run_agents_job)

    # Also schedule at 6:00 PM for more activity
    schedule.every().day.at("18:00").do(run_agents_job)

    print("✓ Scheduler started")
    print("  - Morning run: 09:00")
    print("  - Evening run: 18:00")
    print("")
    print("Press Ctrl+C to stop\n")

    # Run once immediately for testing
    print("Running initial test...")
    run_agents_job()

    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user")

if __name__ == "__main__":
    main()
