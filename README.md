# OutbreakAI – Epidemiology Simulation Assistant

OutbreakAI is an interactive web-based chatbot designed to simulate infectious disease outbreaks using compartmental epidemiological models (SIR, SEIR, SEIRV). Users can explore the spread of diseases, experiment with epidemiological parameters, and understand the dynamics of outbreaks—all in a conversational format

---

## Features

- **Conversational Epidemiology Modeling:**  
  Guides users step-by-step through simulating outbreaks (e.g., COVID-19, influenza, measles).
- **Compartmental Models Supported:**  
  SIR, SEIR, SEIRV (Susceptible, Exposed, Infected, Recovered, Vaccinated).
- **Parameter Customization:**  
  Change population size, transmission rate, recovery rate, initial infected, simulation duration, and more.
- **Tabular Results:**  
  Simulation outputs as easy-to-read plain text tables—no code blocks, no markdown tables.
- **Math Formula Rendering:**  
  Supports LaTeX-style math in chat using KaTeX for clear equations and model explanations.
- **Modern UI:**  
  Responsive, mobile-friendly chat interface with clean message bubbles.
- **Loading Indicator:**  
  Animated "Loading..." during AI response.
- **Session Memory:**  
  Reset button to start fresh simulations.


---

## Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/A-P-U-R-B-O/OutbreakAI.git
cd OutbreakAI
```

### 2. Install dependencies

Make sure you have Python 3.8+ installed.

```bash
pip install -r requirements.txt
```

### 3. Set up your API key

OutbreakAI uses the [Groq API](https://groq.com/) (OpenAI-compatible) for LLM chat.

Set your API key as an environment variable:

```bash
export GROQ_API_KEY="your-groq-api-key"
```

You may also set a `SECRET_KEY` for Flask sessions:

```bash
export SECRET_KEY="your-flask-secret-key"
```

### 4. Run the app

```bash
python app.py
```

The app runs by default on [http://localhost:81](http://localhost:81).

---

## File Structure

```text
OutbreakAI/
├── app.py                # Main Flask backend
├── requirements.txt      # Python dependencies
├── static/
│   ├── style.css         # Custom CSS for UI
├── templates/
│   └── index.html        # Chatbot frontend UI
├── README.md             # Project documentation
Deployment
├── render.yaml

```

---

## Customization

- **Models Supported:**  
  You can further expand the model logic in `app.py` for more compartments or advanced epidemiological features.
- **UI:**  
  Style the chat interface via `static/style.css`.
- **Math & Markdown:**  
  LaTeX math and Markdown supported in both user and bot messages.

---

## Contributing

1. Fork this repo.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes.
4. Submit a pull request!

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Credits

- [Groq API](https://groq.com/)
- [Flask](https://flask.palletsprojects.com/)
- [KaTeX](https://katex.org/)
- [Marked.js](https://marked.js.org/)
- [DOMPurify](https://github.com/cure53/DOMPurify)

---

## Contact

Made by [A-P-U-R-B-O](https://github.com/A-P-U-R-B-O).  
For questions or feedback, open an issue or email via your GitHub profile.
