"""
Mode-B Wegwerf-Harness: A/B-Vergleich zweier lokaler llama.cpp-Modelle.

Voraussetzung: zwei llama-server laufen auf zwei Ports, z.B.
  Terminal 1: llama-server -hf JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M --port 8080
  Terminal 2: llama-server -hf <anderes Modell oder Q6_K-Quant>          --port 8081

Isoliert: keine Imports aus AskValentinAI, keine Tenant-Daten.
Rollback: Ordner loeschen.
"""

import time
from openai import OpenAI

# --- Die zwei Kandidaten. Label nur fuer die Ausgabe, model-Name ist bei
#     llama-server egal (es laeuft ohnehin nur ein Modell pro Port). ---
ENDPOINTS = [
    {"label": "Mellum2 Q4_K_M", "base_url": "http://localhost:8080/v1"},
    {"label": "Mellum2 Q6_K",   "base_url": "http://localhost:8081/v1"},
]


# --- Testaufgaben. Hartkodiert, real. Ersetze/ergaenze durch eigene. ---
PROMPTS = [
    {
        "name": "FastAPI event-loop bug",
        "prompt": (
            "Dies ist ein FastAPI-Endpoint aus einer Produktiv-Anwendung. "
            "Unter Last reagiert der Server traege, obwohl die CPU-Auslastung "
            "niedrig ist und die Route als async deklariert ist. Finde die "
            "Ursache, erklaere WARUM es das Problem verursacht, und gib eine "
            "korrigierte Version an.\n\n"
            "```python\n"
            "import time\n"
            "import requests\n"
            "from fastapi import FastAPI\n"
            "\n"
            "app = FastAPI()\n"
            "\n"
            "@app.get('/enrich/{user_id}')\n"
            "async def enrich(user_id: int):\n"
            "    # externer Dienst, ~400ms Antwortzeit\n"
            "    r = requests.get(f'https://api.internal/profile/{user_id}', timeout=5)\n"
            "    profile = r.json()\n"
            "    time.sleep(0.1)  # kleine lokale Nachbearbeitung\n"
            "    return {'user_id': user_id, 'score': profile['score'] * 2}\n"
            "```"
        ),
    },
    # Weitere echte Aufgaben hier anhaengen:
    # {"name": "...", "prompt": "..."},
]


def ask(base_url: str, prompt: str) -> tuple[str, float]:
    client = OpenAI(base_url=base_url, api_key="not-needed")
    t0 = time.time()
    resp = client.chat.completions.create(
        model="local",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,  # niedrig: deterministischere, vergleichbarere Antworten
    )
    dt = time.time() - t0
    return resp.choices[0].message.content, dt


def main():
    out_path = "results_ab.md"
    with open(out_path, "w") as f:
        f.write("# A/B-Vergleich Coding-Qualitaet\n")

    for task in PROMPTS:
        print(f"\n{'#'*70}\nAUFGABE: {task['name']}\n{'#'*70}")
        with open(out_path, "a") as f:
            f.write(f"\n\n## Aufgabe: {task['name']}\n")
            f.write(f"\n<details><summary>Prompt</summary>\n\n{task['prompt']}\n\n</details>\n")

        for ep in ENDPOINTS:
            print(f"\n--- {ep['label']} ---")
            try:
                answer, dt = ask(ep["base_url"], task["prompt"])
                print(f"({dt:.1f}s)\n{answer}")
                with open(out_path, "a") as f:
                    f.write(f"\n### {ep['label']}  ({dt:.1f}s)\n\n{answer}\n")
            except Exception as e:
                msg = f"FEHLER ({ep['label']}): {e}"
                print(msg)
                with open(out_path, "a") as f:
                    f.write(f"\n### {ep['label']}\n\n`{msg}`\n")

    print(f"\nFertig. Antworten nebeneinander in: {out_path}")


if __name__ == "__main__":
    main()
