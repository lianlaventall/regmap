# Getting Started

This tool extracts and classifies obligation clauses from donor agreement PDFs using AI. Follow these steps to run it on your own machine.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — install and open it before running anything
- A GitHub account
- An Anthropic API key — sign up free at https://console.anthropic.com

---

## Setup (one time only)

**1. Fork the repo**

Go to https://github.com/lianlaventall/regmap and click **Fork** (top right). This creates your own independent copy.

**2. Clone your fork**

```bash
git clone https://github.com/YOUR-USERNAME/regmap.git
cd regmap
```

**3. Create your API key file**

```bash
cp .env.example .env
```

Open `.env` and replace `your-anthropic-api-key-here` with your actual key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

**4. Create the input and output folders**

```bash
mkdir -p input output
```

**5. Build the Docker image**

```bash
docker build -t regmap .
```

This installs Python, all dependencies, and OCR tools inside a container. You only need to do this once (or after pulling updates).

---

## Running the pipeline

**1. Drop your PDF(s) into the `input/` folder**

**2. Run the container**

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  regmap
```

**3. Pick up results from `output/`**

Each PDF produces a `.json` file with all classified clauses.

---

## Editing the taxonomy

The classification rules live in `config/taxonomy.yaml`. Open it in any text editor and modify it — changes take effect the next time you run the container, no rebuild needed.

The taxonomy controls:
- **Tiers** — how obligations are ranked (RESTRICTION, QUALIFIED_RESTRICTION, HIGH_RISK, DECISION)
- **Qualifiers** — phrases that soften a restriction
- **Domains** — the semantic category assigned to each clause (PROCUREMENT, REPORTING, etc.)
- **Dead ends** — terminal restrictions flagged for cross-donor comparison

---

## Troubleshooting

- **Docker not found** — make sure Docker Desktop is running before using the terminal
- **API errors** — double-check your key in `.env`; make sure there are no extra spaces
- **No output** — confirm your PDF is in `input/` and the filename has no special characters
