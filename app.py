import os
import io
import re
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

# SYSTEM PROMPT FOR AI ROLE
SYSTEM_PROMPT = (
    "You are an Epidemiology Simulation Chatbot. "
    "Your primary goal is to assist users in simulating infectious disease outbreaks using compartmental models (e.g., SIR, SEIR, SEIRV). "
    "Always guide the user step-by-step through the simulation process."
    "\n\n"
    "Instructions:\n"
    "1. First, ask the user to specify which disease they want to simulate (for example: COVID-19, influenza, measles, etc.).\n"
    "2. Then, request all necessary epidemiological parameters in a single message. These parameters typically include:\n"
    "   - Population size (N)\n"
    "   - Initial infected (I₀)\n"
    "   - Transmission rate (β)\n"
    "   - Recovery rate (γ)\n"
    "   - Duration of simulation\n"
    "   - Any other relevant model-specific parameters\n"
    "   - Time step (if applicable)\n"
    "   Present default values for each parameter as suggestions, but always allow the user to provide their own values.\n"
    "3. Once the user provides the necessary parameters, perform the simulation using your own reasoning and intelligence.\n"
    "   - Use a plain text table (not Markdown or code blocks) for outputting simulation results. Columns should be separated by spaces and start with a header line.\n"
    "   - For example:\n"
    "     Day Susceptible Infected Recovered\n"
    "     0 49995 5 0\n"
    "     10 47500 1200 1300\n"
    "     ...\n"
    "   - NEVER use Markdown tables, code blocks, or other formatting. Only plain text tables as shown.\n"
    "   - Always output a clean table for every simulation.\n"
    "4. If the user requests a chart, graph, or image, describe the data in a way that can be visualized, and inform the user that a chart will be generated. Ensure the data is in plain text table format.\n"
    "5. Present key takeaways and insights from the simulation. Highlight important statistics such as peak infection, final size, or duration.\n"
    "6. If the user requests a different output (e.g., weekly totals, cumulative cases, line graph), adapt accordingly but always provide the underlying data in plain text table format.\n"
    "\n"
    "General Behavior:\n"
    "- Always ask for clarification if any required information is missing.\n"
    "- Be concise but thorough in explanations.\n"
    "- Never use markdown, code block formatting, or HTML in your tables.\n"
    "- Use clear, plain language throughout your responses.\n"
)

def get_now():
    return datetime.utcnow()

def detect_model_type(text):
    # Returns 'SEIRV', 'SEIR', 'SIRV', 'SIR' based on table headings in text, default SIR
    for line in text.split('\n'):
        l = line.strip()
        if re.match(r"Month\s+S\s+E\s+I\s+R\s+V", l): return "SEIRV"
        if re.match(r"Month\s+S\s+E\s+I\s+R", l): return "SEIR"
        if re.match(r"Month\s+S\s+I\s+R\s+V", l): return "SIRV"
        if re.match(r"Month\s+S\s+I\s+R", l): return "SIR"
    # fallback: try to detect from text
    if "exposed" in text.lower() and "vaccinated" in text.lower(): return "SEIRV"
    if "exposed" in text.lower(): return "SEIR"
    if "vaccinated" in text.lower(): return "SIRV"
    return "SIR"

def extract_table(simulation_text, model_type):
    rows = []
    table_started = False
    variable_order = []
    for line in simulation_text.split('\n'):
        line = line.strip()
        # Accept both "Month" and "Day" as table headers
        if line.startswith("Month") or line.startswith("Day"):
            headers = re.split(r"\s+", line)
            variable_order = headers[1:]
            table_started = True
            continue
        if table_started:
            if re.match(r"^\d+\s+\d+", line):
                cols = re.split(r"\s+", line)
                try:
                    time_idx = int(cols[0])
                    values = []
                    for idx, val in enumerate(cols[1:]):
                        val = val.replace(" ", "")  # Remove unicode thin spaces
                        try:
                            values.append(int(val))
                        except:
                            values.append(float(val))
                    rows.append((time_idx, values))
                except Exception:
                    continue
            elif line == "" or line.lower().startswith("what the numbers"):
                break
    # Transpose to lists
    table = {var: [] for var in variable_order}
    time_points = []
    for time_idx, vals in rows:
        time_points.append(time_idx)
        for i, var in enumerate(variable_order):
            if i < len(vals):
                table[var].append(vals[i])
            else:
                table[var].append(0)
    # Use correct key for time axis
    time_key = "Day" if any(l.startswith("Day") for l in simulation_text.split('\n')) else "Month"
    table[time_key] = time_points
    return table, variable_order
def generate_chart_from_simulation(simulation_text, chart_type="line"):
    model_type = detect_model_type(simulation_text)
    table, variable_order = extract_table(simulation_text, model_type)
    months = table.get("Month", list(range(0, 121, 12)))

    # Default colors for all compartments
    colors = {
        "S": "#1976d2",    # Susceptible: blue
        "E": "#ffb300",    # Exposed: yellow/orange
        "I": "#d32f2f",    # Infected: red
        "R": "#388e3c",    # Removed/Recovered: green
        "V": "#7b1fa2",    # Vaccinated: purple
    }
    labels = {
        "S": "Susceptible",
        "E": "Exposed",
        "I": "Infected",
        "R": "Removed",
        "V": "Vaccinated",
    }

    fig, ax = plt.subplots(figsize=(8,5))
    if chart_type == "bar" and len(variable_order) <= 3:
        # For SIR/SIRV, stacked bar makes sense; for SEIR/SEIRV, use lines for clarity
        bottoms = [0]*len(months)
        for var in variable_order:
            if var == "Month": continue
            ax.bar(months, table.get(var, [0]*len(months)), 
                   bottom=bottoms, color=colors.get(var, None), alpha=0.6, label=labels.get(var, var))
            bottoms = [b + v for b, v in zip(bottoms, table.get(var, [0]*len(months)))]
    else:
        # Always plot each compartment as a line
        for var in variable_order:
            if var == "Month": continue
            ax.plot(months, table.get(var, [0]*len(months)), marker='o', label=labels.get(var, var), color=colors.get(var, None))

    ax.set_xlabel("Month")
    ax.set_ylabel("Number of People")
    ax.set_title(f"{model_type} Simulation")
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
    # --- Ensure system prompt is always present at the start ---
    if "memory" not in session or not session["memory"]:
        session["memory"] = [{"role": "system", "content": SYSTEM_PROMPT}]
    else:
        # If system prompt not present, add it at the start
        if session["memory"][0].get("role") != "system":
            session["memory"].insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    session["memory"].append({"role": "user", "content": user_input})

    try:
        reply = groq_chat(session["memory"])
    except Exception as e:
        reply = f"Sorry, there was an error contacting the LLM: {str(e)}"
        session["memory"].append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    session["memory"].append({"role": "assistant", "content": reply})

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
    simulation_text = request.args.get("data", "")
    chart_type = request.args.get("type", "line")
    image_bytes = generate_chart_from_simulation(simulation_text, chart_type=chart_type)
    return send_file(io.BytesIO(image_bytes), mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
