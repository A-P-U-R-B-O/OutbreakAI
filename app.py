import os
import requests
from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "openai/gpt-oss-120b"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    if "chat_history" not in session:
        session["chat_history"] = []

    session["chat_history"].append({"role": "user", "content": user_input})

    # Replace system prompt for epidemiology simulation chatbot
    full_convo = [{
        "role": "system",
        "content": (
            "You are an Epidemiology Simulation Chatbot. "
            "First, ask the user to specify which disease they want to simulate (e.g., COVID-19, influenza, measles, etc.). "
            "Then, request all necessary epidemiological parameters in one message (such as population size, initial infected, transmission rate, recovery rate, duration of simulation, etc.). "
            "Once the user provides the inputs, calculate the simulated disease spread and present the results using your own reasoning and intelligence. "
            "Guide the user through the process step by step, ensuring you gather all needed data before running the simulation."
        )
    }]
    full_convo.extend(session["chat_history"])

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": full_convo[-10:],
        "temperature": 0.8
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            session["chat_history"].append({"role": "assistant", "content": reply})
            return jsonify({"reply": reply})
        else:
            print("Groq error:", response.status_code, response.text)
            return jsonify({"reply": "Oops! Something went wrong on the server."})
    except Exception as e:
        print("Server crash:", e)
        return jsonify({"reply": "Unexpected server error occurred."})

@app.route("/reset", methods=["POST"])
def reset():
    session.pop("chat_history", None)
    return jsonify({"reply": "Memory wiped. Fresh start!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
