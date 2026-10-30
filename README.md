# Multi-Objective Optimization Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Framework: Dash & Pymoo](https://img.shields.io/badge/Framework-Dash%20%7C%20Pymoo-orange.svg)](https://pymoo.org/)

An interactive web-based graphical platform for modeling, solving, and analyzing multi-objective optimization problems using **NSGA-II**. Powered by **Plotly Dash** and **Pymoo**.

---

## Overview

Multi-objective optimization often requires manual scripting and post-processing of non-dominated Pareto sets. This platform provides an intuitive, end-to-end web interface for formulating optimization problems, configuring genetic operators, executing **NSGA-II** in real-time, and evaluating Pareto-optimal trade-offs.

### Key Capabilities

- **Problem Modeling**: Define continuous, integer, and binary decision variables, multiple objective functions, and inequality/equality constraints using safe mathematical expressions (arithmetic, `x[i]` indexing and functions such as `sin`, `exp`, `sqrt`, `sum`).
- **Optimization Algorithm**: Powered by **NSGA-II** (Non-dominated Sorting Genetic Algorithm II) with configurable population size, generations, Simulated Binary Crossover (SBX), and Polynomial Mutation (PM).
- **Dynamic Optimization**: Includes benchmark support for dynamic environments (such as the CEC 2018 benchmark suite) with time-dependent environment tracking.
- **Visual Analytics**: Interactive 2D/3D Pareto front scatter plots, parallel coordinate plots, and live convergence tracking (Hypervolume, Spread, Spacing).
- **Decision Support**: Sortable, filterable table of Pareto-optimal solutions with their decision variables.
- **Persistence & Export**: Download the experiment (problem, settings and results) as JSON, export the Pareto set to CSV, generate a standalone pymoo script, and inspect individual candidate solutions.

---

## Architecture & Project Structure

```
moo-gui-platform/
├── assets/                 # Themes (dark/light), typography, and custom CSS
├── benchmarks/             # ISVM-DMOEA benchmark on DF1-DF14 and paper-style result tables
├── cec2018_dmop/           # CEC2018 dynamic benchmarks (DF1-DF14, via pymoo) with the competition's time schedule
├── database/               # User state persistence (users.json)
├── dmoea/                  # ISVM-DMOEA prediction for dynamic problems (SMOTE or LoRAS oversampling)
├── examples/               # Programmatic usage and automation scripts
├── gui/                    # Dash application package
│   ├── auth/               # Authentication and password hashing
│   ├── callbacks/          # Reactive UI callbacks and state synchronization
│   ├── core/               # Optimization engine and experiment state manager
│   └── layouts/            # Page layouts (problem, algorithm, visualizer, results)
├── tests/                  # Unit and integration test suite
├── .github/workflows/      # Automated CI/CD pipeline
├── Dockerfile              # Multi-stage production container
├── docker-compose.yml      # Local and cloud compose configuration
├── expression_parser.py    # AST-based safe mathematical formula evaluator
├── generic_problem.py      # Dynamic pymoo problem wrapper
├── engineering_problem.py  # Standard engineering problem templates
├── main.py                 # Application entry point and WSGI server export
├── Procfile                # PaaS deployment specification
└── requirements.txt        # Core dependencies
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- `pip` package manager

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kushagra0526/moo-gui-platform.git
   cd moo-gui-platform
   ```

2. **Create and activate a virtual environment** *(optional but recommended)*:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application**:
   ```bash
   python main.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:8080
   ```

### Default Credentials

The platform comes initialized with a local test account:
- **Email**: `test@test.com`
- **Password**: `TestPassword123!`

*(You can also register a new account directly from the login page).*

Before deploying publicly, remove this test account from `database/users.json`: its password is published here, and sign-up is open to anyone who can reach the site.

---

## Deployment

### Docker (Recommended)

Run with Docker Compose:
```bash
docker compose up --build -d
```

Or build and run the Docker image directly:
```bash
docker build -t moo-gui-platform .
docker run -p 8080:8080 moo-gui-platform
```

### Production WSGI (Linux / Cloud VM)

The application exports a standard WSGI `server` object in `main.py`:
```bash
gunicorn --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:8080 main:server
```

Keep a single worker: a running optimization lives in that process's memory, so a second worker would not see it.

### Cloud PaaS (Render / Railway / Fly.io)

- The repository includes a `Procfile` and dynamic `PORT` environment variable binding.
- Connect your GitHub repository to Render or Railway as a **Web Service**; build and start commands will be detected automatically.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` / `MOO_GUI_PORT` | `8080` | Web server port |
| `MOO_GUI_HOST` | `0.0.0.0` | Bind host address |
| `MOO_GUI_DEBUG` | `false` | Enable Dash hot-reloading |
| `MOO_GUI_SECRET_KEY` | random per start | Signs the login session cookie. Set it so logins survive restarts |

---

## Dynamic Prediction Module (`dmoea/`)

Implements ISVM-DMOEA (Xu et al., *IEEE TEVC* 26(4), 2022) on the CEC2018 DF problems with NSGA-II as the
static optimizer. When the environment changes, an RBF-SVM trained on past Pareto-optimal solutions picks the
next initial population. The oversampling step can use SMOTE (as in the paper) or LoRAS
(Bej et al., *Machine Learning* 110, 2021).

```python
from dmoea import run
result = run(2, nt=10, taut=10, strategy="isvm", oversampling="loras", seed=1)
print(result["migd"], result["mhv"])
```

In the app, the **Dynamic Prediction** page runs random restart, ISVM-SMOTE and ISVM-LoRAS on one DF problem
and shows their IGD per environment with a MIGD/MHV summary.

To reproduce the paper's experiments (random restart vs ISVM-SMOTE vs ISVM-LoRAS, 14 problems × 3
configurations; results and tables are written to `experiments/`):

```bash
python benchmarks/isvm_benchmark.py run --runs 20 --workers 4   # resumable
python benchmarks/isvm_benchmark.py tables
```

Differences from the paper: the incremental SVM retrains on the previous support vectors plus new samples
instead of the exact Cauwenberghs–Poggio update, variables are scaled to [0, 1] before oversampling, and the
prediction step falls back to the best-scoring candidates when too few random points are classified optimal.

---

## Running Tests

Execute the automated test suite using Python's built-in test runner:

```bash
python -m unittest discover tests
```

To run the programmatic optimization example:
```bash
python examples/basic_example.py
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
