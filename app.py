import os
import io
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_session import Session
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = "openai/gpt-oss-120b"

def get_now():
    return datetime.utcnow()

def extract_sir_table(simulation_text):
    import re
    rows = []
    table_started = False
    for line in simulation_text.split('\n'):
        line = line.strip()
        if re.match(r"Month\s+S\s+I\s+R", line):
            table_started = True
            continue
        if table_started:
            if re.match(r"^\d+\s+\d+", line):
                cols = re.split(r"\s+", line)
                if len(cols) >= 4:
                    try:
                        month = int(cols[0])
                        s = int(cols[1].replace(" ", ""))
                        i = int(cols[2].replace(" ", ""))
                        r = int(cols[3].replace(" ", ""))
                        rows.append((month, s, i, r))
                    except Exception:
                        continue
            elif line == "" or line.lower().startswith("what the numbers"):
                break
    return rows

def generate_chart_from_simulation(simulation_text, chart_type="line"):
    sir_table = extract_sir_table(simulation_text)
    if sir_table and len(sir_table) > 0:
        months = [row[0] for row in sir_table]
        S = [row[1] for row in sir_table]
        I = [row[2] for row in sir_table]
        R = [row[3] for row in sir_table]
    else:
        # fallback dummy data
        months = list(range(0, 121, 12))
        S = [1949, 1854, 1640, 1310, 876, 423, 90, 8, 0, 0, 0]
        I = [50, 135, 311, 521, 714, 796, 714, 489, 285, 164, 95]
        R = [0, 9, 48, 168, 409, 780, 1195, 1502, 1714, 1835, 1904]

    fig, ax = plt.subplots(figsize=(8,5))
    if chart_type == "bar":
        width = 3 if len(months) > 10 else 0.5
        ax.bar(months, S, width=width, color="#1976d2", alpha=0.6, label="Susceptible")
        ax.bar(months, I, width=width, color="#d32f2f", alpha=0.6, label="Infected", bottom=S)
        ax.bar(months, R, width=width, color="#388e3c", alpha=0.6, label="Removed", bottom=[s+i for s, i in zip(S, I)])
    else:
        ax.plot(months, S, 'b-', marker='o', label="Susceptible")
        ax.plot(months, I, 'r-', marker='o', label="Infected")
        ax.plot(months, R, 'g-', marker='o', label="Removed")
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of People")
    ax.set_title("HIV/AIDS SIR Simulation")
    ax.legend()
    plt.tight_layout()
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close(fig)
    img_bytes.seek(0)
    return img_bytes.read()

def groq_chat(messages, model=MODEL):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

@app.route("/", methods=["GET"])
def index():
    session["memory"] = []
    return render_template("index.html", now=get_now())

@app.route("/reset", methods=["POST"])
def reset():
    session["memory"] = []
    return jsonify({"reply": "Memory wiped. Fresh start!"})

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    if "memory" not in session:
        session["memory"] = []
    session["memory"].append({"role": "user", "content": user_input})

    try:
        reply = groq_chat(session["memory"])
    except Exception as e:
        reply = f"Sorry, there was an error contacting the LLM: {str(e)}"
        session["memory"].append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    session["memory"].append({"role": "assistant", "content": reply})

    # Visualization detection logic
    wants_visualization = any(word in user_input.lower() for word in [
        "show", "plot", "graph", "chart", "visualize", "draw"
    ])
    chart_type = "bar" if any(word in user_input.lower() for word in ["bar chart", "bar graph"]) else "line"

    image_base64 = None
    if wants_visualization:
        image_bytes = generate_chart_from_simulation(reply, chart_type=chart_type)
        import base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    return jsonify({
        "reply": reply,
        "image": image_base64
    })

@app.route("/image")
def image():
    # For direct image download/view (not used by default, but can be useful)
    simulation_text = request.args.get("data", "")
    chart_type = request.args.get("type", "line")
    image_bytes = generate_chart_from_simulation(simulation_text, chart_type=chart_type)
    return send_file(io.BytesIO(image_bytes), mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
