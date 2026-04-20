import json
import csv

input_file = "gig3_3d_leads_20260420_012832.json"
output_file = "GIG3_FULL_LEAD_LIST.csv"

try:
    with open(input_file, "r", encoding="utf-8") as f:
        leads = json.load(f)
    
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(["Lead Name", "Subreddit", "Project Title", "URL", "Context", "Outreach Message"])
        
        for lead in leads:
            writer.writerow([
                lead.get("author"),
                lead.get("subreddit"),
                lead.get("title"),
                lead.get("url"),
                lead.get("body_preview", "").replace("\n", " ")[:200],
                lead.get("outreach_message", "").replace("\n", " ")
            ])
            
    print(f"Successfully converted {len(leads)} leads to {output_file}")
except Exception as e:
    print(f"Error: {e}")
