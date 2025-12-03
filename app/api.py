# --- Filename: api.py (Enhanced) ---

from dotenv import load_dotenv
import os
import logging
from typing import TypedDict, List, Union

from flask import Flask, request, jsonify
from flask_cors import CORS

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq


# -------------------------
# 1️⃣ Setup & Logging
# -------------------------
load_dotenv(".env")

logging.basicConfig(
    level=logging.INFO,
    format="🔹 [%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("🚨 Missing GROQ_API_KEY in .env")

# LLM Config
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.3
)

# -------------------------
# 2️⃣ Load FAISS Index
# -------------------------
INDEX_PATH = "index"
logging.info("🔍 Loading FAISS index...")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
try:
    db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={"k": 3})
    logging.info("✅ FAISS index loaded successfully.")
except Exception as e:
    logging.error(f"Failed to load FAISS index: {e}")
    retriever = None


# -------------------------
# 3️⃣ Define Graph State
# -------------------------
class ChatState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage]]
    context: str
    intent: str


# -------------------------
# 4️⃣ Node Definitions
# -------------------------
def classify_intent_node(state: ChatState):
    """Classify user intent based on last message."""
    query = state["messages"][-1].content.strip()

    classification_prompt = (
        "Classify the user's query into one of these categories:\n"
        "[greeting, services, contact, appointment, hours, location, founder, motto, "
        "staffing, industries, experience, policy, general_qa]\n\n"
        f"User Query: {query}\nCategory:"
    )

    try:
        response = llm.invoke(classification_prompt)
        intent = response.content.strip().lower()

        # Clean + fallback logic
        keywords = {
            "greeting": "greeting", "hello": "greeting",
            "service": "services", "offer": "services",
            "contact": "contact", "email": "contact",
            "appointment": "appointment", "book": "appointment",
            "hour": "hours", "time": "hours",
            "location": "location", "address": "location",
            "founder": "founder", "motto": "motto",
            "staff": "staffing", "industry": "industries",
            "experience": "experience", "policy": "policy"
        }

        # Try fuzzy matching
        for key, val in keywords.items():
            if key in intent or key in query.lower():
                state["intent"] = val
                break
        else:
            state["intent"] = "general_qa"

        logging.info(f"🤖 Classified intent: {state['intent']}")
        return state

    except Exception as e:
        logging.error(f"Intent classification failed: {e}")
        state["intent"] = "general_qa"
        return state


# --- Quick Response Nodes ---
def reply_node(state: ChatState, text: str):
    state["messages"].append(AIMessage(content=text))
    return state


def handle_greeting_node(state: ChatState):
    return reply_node(state, "Hey there! 👋 I'm Tara, your SLCI assistant. How can I help?")


def handle_services_node(state: ChatState):
    return reply_node(state,
        "We offer:\n• ESI & EPF Compliance\n• Labour Law Compliances\n• HR Solutions\n• Payroll Services\n• Staffing"
    )


def handle_contact_node(state: ChatState):
    return reply_node(state,
        "📞 Call: +91 9999329153 or 011-41609501\n✉️ Email: contact@slci.in"
    )


def handle_appointment_node(state: ChatState):
    return reply_node(state,
        "📅 Book an appointment by calling +91 9999329153 or emailing contact@slci.in."
    )


def handle_hours_node(state: ChatState):
    return reply_node(state, "🕒 Office Hours: Monday–Saturday, 9:30 AM – 6:30 PM.")


def handle_location_node(state: ChatState):
    return reply_node(state, "📍 Address: 83, DSIDC Complex, Okhla Industrial Area Phase 1, New Delhi - 110020.")


def handle_founder_node(state: ChatState):
    return reply_node(state, "👔 Founded by Mr. S.K. Sharma — 38+ years of experience in compliance & HR law.")


def handle_motto_node(state: ChatState):
    return reply_node(state, "💼 Our Motto: 'Do Business, Not HR.'")


def handle_staffing_node(state: ChatState):
    return reply_node(state, "🤝 Staffing services include recruitment, verification, and third-party manpower.")


def handle_industries_node(state: ChatState):
    return reply_node(state, "🏭 We serve manufacturing, logistics, IT, healthcare, and retail industries.")


def handle_experience_node(state: ChatState):
    return reply_node(state, "📚 Over 38 years of domain experience in law, compliance & HR services.")


def handle_policy_node(state: ChatState):
    return reply_node(state, (
        "🔐 **Privacy Policy**\n\n"
        "• Data We Collect: Only necessary client & compliance details.\n"
        "• How We Use It: Exclusively for representation, billing & communication.\n"
        "• Sharing: Never sold. Shared only with consent or legal requirement.\n"
        "• Security: Protected under strong confidentiality measures."
    ))


# --- RAG Nodes ---
def retrieve_node(state: ChatState):
    """Retrieve relevant docs from FAISS."""
    query = state["messages"][-1].content
    if not retriever:
        state["context"] = ""
        return state

    try:
        docs = retriever.invoke(query)
        context = "\n\n".join([d.page_content for d in docs])
        state["context"] = context
        return state
    except Exception as e:
        logging.error(f"Retrieval error: {e}")
        state["context"] = ""
        return state


def generate_node(state: ChatState):
    """Generate final response with short, clear, point-wise format."""
    query = state["messages"][-1].content.lower()
    context = state.get("context", "")

    # Detect if user wants detailed explanation
    wants_detail = any(word in query for word in 
                       ["explain", "detail", "describe", "kyu", "kaise", "samjhao"])

    # Short reply prompt (default)
    short_prompt = f"""
You are Tara, the SLCI Assistant.

RULES:
1. Give very short, simple, clear answers.
2. Use bullet points (•) for clarity.
3. No long paragraphs.
4. Speak in the same language the user used (Hindi/English/Hinglish).
5. Keep tone friendly and professional.
6. If information is not in context, still give a short general helpful answer.

Context:
{context}

User: {query}
Answer in short, point-wise:
"""

    # Detailed reply prompt (ONLY when user asks)
    detailed_prompt = f"""
You are Tara, the SLCI Assistant.

User is asking for a detailed explanation.

RULES:
1. Give a clear, structured, easy explanation.
2. Use headings + bullet points.
3. Use simple language (Hindi/English/Hinglish same as user).
4. Stay professional and helpful.
5. Use context properly.

Context:
{context}

User: {query}
Explain in a detailed but easy-to-understand way:
"""

    # Choose prompt
    prompt = detailed_prompt if wants_detail else short_prompt

    # Generate reply
    try:
        response = llm.invoke(prompt)
        reply = getattr(response, "content", str(response))
    except Exception as e:
        reply = f"⚠️ Sorry, I faced an issue generating an answer: {e}"

    state["messages"].append(AIMessage(content=reply))
    return state

    """Generate final response with optimized conversational behavior."""
    query_raw = state["messages"][-1].content
    query = query_raw.lower()
    context = state.get("context", "")

    # ----------- DETECT USER LANGUAGE -----------
    # Hinglish, Hindi, English auto-detect
    is_hindi = any(ch in query for ch in "अआइईउऊएऐओऔकखगघचछजझटठडढतथदधनपफबभमयरलवशषसह")
    if is_hindi:
        lang_style = "Reply in simple Hinglish/Hindi depending on user style."
    else:
        lang_style = "Reply in clean, simple English or Hinglish matching user tone."

    # ----------- DETECT EXPLANATION INTENT -----------
    wants_explanation = any(w in query for w in [
        "explain", "detail", "samjhao", "samjha", "samjha do",
        "detail me", "proper way", "deep", "describe", "process bataye"
    ])

    # ----------- QUICK MODE = SHORT CLEAN ANSWERS -----------
    if not wants_explanation:
        style = (
            "Keep reply SHORT (1–2 lines only), polite, crisp, human-like.\n"
            "No long stories. No paragraphs. No over-explanation.\n"
            "Tone = Friendly SLCI staff. Natural speaking style.\n"
            f"{lang_style}"
        )
    else:
        # ----------- EXPLANATION MODE -----------
        style = (
            "User wants a detailed explanation.\n"
            "Give structured explanation:\n"
            "- Use bullet points\n"
            "- Keep professional tone\n"
            "- Clear, step-by-step\n"
            "- Include examples when needed\n"
            f"{lang_style}"
        )

    # ----------- FINAL PROMPT -----------
    prompt = (
    "You are Tara, an SLCI assistant.\n"
    "RULES:\n"
    "1. Default answers must be VERY short, simple, and in clear Hinglish.\n"
    "2. Always reply in point-wise format (• bullets) unless user says 'explain', 'detail', 'describe'.\n"
    "3. If user says 'explain', then give: \n"
    "   - Proper headings\n"
    "   - Clear bullets\n"
    "   - Easy professional tone\n"
    "4. NEVER give long paragraphs by default.\n"
    "5. Reply in the same language style as user (Hindi/English/Hinglish mix).\n\n"
    f"Context:\n{context}\n\n"
    f"User Query: {query}\n\n"
    "Give the best response following the rules above."
)


    try:
        response = llm.invoke(prompt)
        reply = getattr(response, "content", str(response))
    except Exception as e:
        reply = f"⚠️ Sorry, an error occurred: {e}"

    state["messages"].append(AIMessage(content=reply))
    return state
# -------------------------
# 5️⃣ LangGraph Build
# -------------------------
graph = StateGraph(ChatState)

nodes = {
    "classify_intent": classify_intent_node,
    "retrieve": retrieve_node,
    "generate": generate_node,
    "greeting": handle_greeting_node,
    "services": handle_services_node,
    "contact": handle_contact_node,
    "appointment": handle_appointment_node,
    "hours": handle_hours_node,
    "location": handle_location_node,
    "founder": handle_founder_node,
    "motto": handle_motto_node,
    "staffing": handle_staffing_node,
    "industries": handle_industries_node,
    "experience": handle_experience_node,
    "policy": handle_policy_node,
}

for name, func in nodes.items():
    graph.add_node(name, func)

graph.set_entry_point("classify_intent")

def route_after_classification(state: ChatState):
    return state.get("intent", "general_qa")

graph.add_conditional_edges("classify_intent", route_after_classification, {
    "general_qa": "retrieve", **{k: k for k in nodes if k != "classify_intent"}
})
graph.add_edge("retrieve", "generate")

for n in nodes:
    if n not in ("classify_intent", "retrieve"):
        graph.add_edge(n, END)
graph.add_edge("generate", END)

checkpointer = MemorySaver()
workflow = graph.compile(checkpointer=checkpointer)


# -------------------------
# 6️⃣ Flask API
# -------------------------
flask_app = Flask(__name__)
CORS(flask_app)

@flask_app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        user_message = data.get("message")
        session_id = data.get("session_id")

        if not user_message or not session_id:
            return jsonify({"error": "Missing 'message' or 'session_id'"}), 400

        config = {"configurable": {"thread_id": session_id}}
        state = {"messages": [HumanMessage(content=user_message)], "context": "", "intent": ""}

        result = workflow.invoke(state, config=config)
        ai_reply = result["messages"][-1].content

        # logging.info(f"💬 User: {user_message}\n🤖 Bot: {ai_reply}")
        return jsonify({"reply": ai_reply})

    except Exception as e:
        logging.error(f"Chat endpoint failed: {e}")
        return jsonify({"error": str(e)}), 500


# -------------------------
# 7️⃣ Exported Objects (for main.py)
# -------------------------
__all__ = ["workflow", "HumanMessage"]

