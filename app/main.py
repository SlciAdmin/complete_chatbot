import os
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from wages_api import fetch_minimum_wage
from api import workflow, HumanMessage

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)

CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="🔹 [%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S"
)

STATE_LIST = [
    "Andaman And Nicobar Islands",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Gujarat",
    "Jammu and Kashmir",
    "Delhi",
    "Daman and Diu",
    "Chattisgarh",
    
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        user_message = data.get("message", "").lower()
        session_id = data.get("session_id")

        if not user_message or not session_id:
            return jsonify({"error": "Missing 'message' or 'session_id'"}), 400

        # Wage Intent Detection
        wage_keywords = ["minimum wage", "minimum wages", "wages"]
        if any(keyword in user_message for keyword in wage_keywords):

            for item in STATE_LIST:
                if item.lower() in user_message:
                    wage_data = fetch_minimum_wage(item)
                    return jsonify(wage_data)

            return jsonify({"reply": "Please specify a state like Bihar, Assam, etc."})

        # AI Fallback
        config = {"configurable": {"thread_id": session_id}}
        state = {"messages": [HumanMessage(content=user_message)], "context": "", "intent": ""}

        result = workflow.invoke(state, config=config)
        ai_reply = result["messages"][-1].content
        return jsonify({"reply": ai_reply})

    except Exception as e:
        logging.error(f"Chat failed: {e}")
        return jsonify({"error": str(e)}), 500

    try:
        data = request.json or {}
        user_message = data.get("message", "").lower()
        session_id = data.get("session_id")

        if not user_message or not session_id:
            return jsonify({"error": "Missing 'message' or 'session_id'"}), 400

        # Wage intent check
        wage_keywords = ["minimum wage", "minimum wages", "min wage", "wages"]

        if any(keyword in user_message for keyword in wage_keywords):
            detected_state = None
            for state in STATE_LIST:
                if state.lower() in user_message:
                    detected_state = state
                    break

            if detected_state:
                wages_data = fetch_minimum_wage(detected_state)

                if not wages_data:
                    return jsonify({"reply": f"⚠ No wage data found for {detected_state}"}), 404

                meta = wages_data.get("meta_data", {})
                table = meta.get("table_data", [])
                effective = meta.get("effective_from", "NA")
                updated = meta.get("updated_as_on", "NA")

                reply_text = (
                    f"📍 Minimum Wages for **{detected_state}**\n\n"
                    f"🗓 Effective From: {effective}\n"
                    f"📌 Updated As On: {updated}\n\n"
                    f"📊 Wage Structure:\n{table}"
                )

                return jsonify({"reply": reply_text, "data": wages_data})

            return jsonify({"reply": "Please specify a state like Bihar, Assam, etc."})

        # --- AI WORKFLOW FALLBACK ---
        config = {"configurable": {"thread_id": session_id}}
        state = {"messages": [HumanMessage(content=user_message)], "context": "", "intent": ""}
        result = workflow.invoke(state, config=config)
        ai_reply = result["messages"][-1].content

        return jsonify({"reply": ai_reply})

    except Exception as e:
        logging.error(f"Chat failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/min-wage", methods=["GET"])
def min_wage_route():
    state = request.args.get("state")
    if not state:
        return jsonify({"error": "Missing 'state' parameter"}), 400

    return jsonify(fetch_minimum_wage(state))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
