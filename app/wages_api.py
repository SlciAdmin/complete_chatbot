import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_URL = os.getenv("minimum_wage_api_key")

def fetch_minimum_wage(state_query):
    try:
        response = requests.get(API_URL)
        data = response.json()

        state_query_lower = state_query.lower()

        for item in data:

            # --- Match State ---
            if state_query_lower in item["state_name"].lower() or state_query_lower in item["api_slug"].lower():

                meta = item.get("meta_data", {})
                table = meta.get("table_data", [])

                # Extract additional metadata
                state_name = meta.get("state_name", item["state_name"])
                act_name = meta.get("act_name", "NA")
                category_count = meta.get("category_count", "NA")
                zone_info = meta.get("zones", "NA")
                effective = meta.get("effective_from", "NA")
                updated = meta.get("updated_as_on", "NA")
                da = meta.get("dearness_allowance", "NA")
                pdf_url = meta.get("pdf_url", None)

                # -------------------------
                # Format table into text
                # -------------------------
                table_text = "📊 **Wage Structure**\n\n"
                for row in table:
                    table_text += " | ".join(row) + "\n"

                # -------------------------
                # Build Final Output
                # -------------------------

                reply_text = (
                    f"📍 **Minimum Wages for {state_name}**\n\n"
                    f"📘 **Act / Rule**: {act_name}\n"
                    f"🏷 **Category Count**: {category_count}\n"
                    f"🗺 **Zones**: {zone_info}\n"
                    f"🧮 **Dearness Allowance (DA)**: {da}\n\n"
                    f"🗓 **Effective From**: {effective}\n"
                    f"📌 **Updated As On**: {updated}\n\n"
                    f"{table_text}\n"
                )

                if pdf_url:
                    reply_text += f"📄 **Govt. Notification PDF**: {pdf_url}"

                return {
                    "reply": reply_text,
                    "table": table,
                    "meta": {
                        "state": state_name,
                        "act_name": act_name,
                        "category_count": category_count,
                        "zones": zone_info,
                        "effective_from": effective,
                        "updated_as_on": updated,
                        "da": da,
                        "pdf_url": pdf_url
                    }
                }

        return {"reply": "❌ State not found. Please check the state name."}

    except Exception as e:
        return {"reply": f"⚠ Error fetching data: {str(e)}"}
