#!/usr/bin/env python3
"""
REVENUE BLITZ — Opens all bid targets in browser + copies bid text to clipboard
Run this script and it opens all 7 gig URLs for rapid bidding.
"""
import webbrowser
import time
import subprocess

# All target URLs — highest priority first
TARGETS = [
    {
        "name": "GIG #8: AI Agent Developer (High Priority)",
        "url": "https://reddit.com/r/hiring/comments/1spnuzg/hiring_looking_for_ai_agent_developer_automation/",
        "action": "DM u/Standard-House-8469 with Blueprint v5 pitch",
    },
    {
        "name": "GIG #3: Outreach ($20+/project) — ZERO BIDS!",
        "url": "https://www.reddit.com/r/slavelabour/comments/1sq9jzw/task_looking_for_outreach_help_find_contact/",
        "action": "DM u/BEEG_-BEEG_YOSHI",
    },
    {
        "name": "GIG #1: Video Editor ($50) — LOW competition",
        "url": "https://www.reddit.com/r/slavelabour/comments/1sqeu4f/task_video_editor_needed/",
        "action": "Comment $bid + DM u/jojoaj35",
    },
    {
        "name": "GIG #2: AI Video ($25)",
        "url": "https://www.reddit.com/r/slavelabour/comments/1sq59ft/task_25_generate_a_4050_second_ai_video/",
        "action": "Comment $bid + DM u/Burnttoastmilkshake",
    },
    {
        "name": "GIG #4: Social Media ($100/month)",
        "url": "https://www.reddit.com/r/slavelabour/comments/1sprlyr/task_bulk_social_media_content_creation/",
        "action": "Comment $bid + DM u/eddy14207",
    },
    {
        "name": "GIG #5: Reddit Posting ($20/week)",
        "url": "https://www.reddit.com/r/forhire/comments/1sqh8sf/hiring_need_people_to_handle_reddit_posting_easy/",
        "action": "Comment interested + DM u/Potential-Cow-1",
    },
    {
        "name": "GIG #6: YouTube Editor ($50-$150/edit)",
        "url": "https://www.reddit.com/r/slavelabour/comments/1sozn30/task_creative_video_editor_needed_for_highenergy/",
        "action": "Comment $bid + DM u/Heidi_PB",
    },
    {
        "name": "GIG #7: Lead Gen ($20/hr)",
        "url": "https://www.reddit.com/r/forhire/comments/1spxgq1/hiring_lead_generation_sales_research_specialist/",
        "action": "DM u/Gullible_Drag_3515",
    },
]

def main():
    print("=" * 60)
    print("   REVENUE BLITZ - OPENING ALL GIG TARGETS")
    print("=" * 60)
    print()
    
    for i, target in enumerate(TARGETS, 1):
        print(f"  [{i}/7] {target['name']}")
        print(f"        -> {target['action']}")
        print(f"        -> {target['url']}")
        webbrowser.open(target['url'])
        time.sleep(1.5)  # Don't open all at once
        print()
    
    print("=" * 60)
    print("  DONE - ALL 7 TABS OPENED!")
    print()
    print("  QUICK REFERENCE:")
    print("  * For r/slavelabour posts: Comment '$bid' first, then DM")
    print("  * For r/forhire posts: Comment or DM directly")
    print("  * All DM templates are in: revenue_battleplan.md")
    print("=" * 60)
    print()
    print("  TIP: Start with GIG #3 (outreach) - ZERO competition!")
    print("       Then GIG #1 (video) - only 2 bids, $50 payout.")

if __name__ == "__main__":
    main()
