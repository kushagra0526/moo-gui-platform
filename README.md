# Multi-Objective Optimization Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Framework: Dash & Pymoo](https://img.shields.io/badge/Framework-Dash%20%7C%20Pymoo-orange.svg)](https://pymoo.org/)

An interactive web-based graphical platform for modeling, solving, and analyzing multi-objective, many-objective, and dynamic optimization problems. Powered by **Plotly Dash** and **Pymoo**.

---

## Overview

Evolutionary multi-objective optimization often requires manual scripting and post-processing of Pareto-optimal sets. This platform provides an end-to-end interface for formulating arbitrary optimization problems, tuning genetic operators, executing optimizations in real-time, and evaluating solutions through multi-criteria decision making.

### Key Capabilities

- **Problem Modeling**: Define decision variables (continuous, integer, binary), multiple objective functions, and constraints using safe mathematical expressions.
- **Algorithm Support**: Out-of-the-box integration with NSGA-II, NSGA-III, MOEA/D, RM-MEDA, and MOPSO.
- **Dynamic Optimization**: Includes the complete **CEC 2018 Dynamic Multi-Objective Problem suite (DF1–DF14)** with real-time environment shift tracking.
- **Visual Analytics**: Interactive 2D/3D Pareto front scatter plots, parallel coordinate plots for high-dimensional objectives, and live convergence metrics (Hypervolume, IGD).
- **Decision Support**: Integrated TOPSIS ranking, weighted sum, aspiration-level filtering, and solution trade-off exploration.
- **Persistence & Export**: Save and load complete experiment states in JSON/YAML, export Pareto fronts to CSV, and export publication-ready figures.

---

## Architecture & Project Structure

```
moo-gui-platform/
├── assets/                 # Themes (dark/light), typography, and custom CSS
├── cec2018_dmop/           # Dynamic benchmark suite (DF1-DF14) and time generators
├── database/               # User state persistence (users.json)
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
├── requirements.txt        # Core dependencies
└── setup.py                # Package metadata and installation script
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
gunicorn --workers 4 --threads 2 --timeout 120 --bind 0.0.0.0:8080 main:server
```

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
| `MOO_GUI_TIMEOUT` | `60` | Optimization timeout in minutes |

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
