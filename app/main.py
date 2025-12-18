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
    "Andaman and Nicobar Islands",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli",
    "Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal"
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        user_message = data.get("message", "").lower()
        session_id = data.get("session_id")

        if not user_message or not session_id:
            return jsonify({"error": "Missing 'message' or 'session_id'"}), 400

        wage_keywords = ["minimum wage", "minimum wages", "min wage", "wages"]

        if any(keyword in user_message for keyword in wage_keywords):
            for state in STATE_LIST:
                if state.lower() in user_message:
                    return jsonify(fetch_minimum_wage(state))

            return jsonify({"reply": "Please specify a state like Delhi, Bihar, Assam etc."})

        config = {"configurable": {"thread_id": session_id}}
        state_data = {
            "messages": [HumanMessage(content=user_message)],
            "context": "",
            "intent": ""
        }

        result = workflow.invoke(state_data, config=config)
        ai_reply = result["messages"][-1].content

        return jsonify({"reply": ai_reply})

    except Exception as e:
        logging.exception("Chat failed")
        return jsonify({"error": str(e)}), 500


@app.route("/min-wage", methods=["GET"])
def min_wage_route():
    state = request.args.get("state")
    if not state:
        return jsonify({"error": "Missing 'state' parameter"}), 400

    return jsonify(fetch_minimum_wage(state))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
