import os
import io
import base64
import requests
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "openai/gpt-oss-120b"

def generate_chart_from_simulation(simulation_text):
    """
    Dummy parser: looks for lines like "Day X: infected Y"
    Replace with your own parsing logic based on simulation_text format.
    """
    days = []
    infected = []
    for line in simulation_text.split('\n'):
        if "Day" in line and "infected" in line:
            parts = line.split()
            try:
                day = int(parts[1].replace(":", ""))
                num = int(parts[-1])
                days.append(day)
                infected.append(num)
            except:
                continue
    # If nothing parsed, make a dummy graph
    if not days or not infected:
        days = list(range(1, 11))
        infected = [10 * i**2 for i in days]
    fig, ax = plt.subplots()
    ax.plot(days, infected, marker='o')
    ax.set_xlabel("Day")
    ax.set_ylabel("Number of Infected")
    ax.set_title("Simulated Disease Spread")
    img_bytes = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_bytes, format='png')
    plt.close(fig)
    img_bytes.seek(0)
    return img_bytes.read()

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
            "If the user requests a graph, chart, or image, describe the data in a way that can be visualized and inform the user a chart will be generated. "
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

            # Check if user asked for a graph/chart/image in their last message
            wants_visualization = any(word in user_input.lower() for word in ["graph", "chart", "image", "plot", "visual"])
            if wants_visualization:
                image_bytes = generate_chart_from_simulation(reply)
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                return jsonify({"reply": reply, "image": image_base64})
            else:
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
