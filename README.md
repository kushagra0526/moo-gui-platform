# Multi-Objective Optimization GUI

A research-grade graphical user interface for multi-objective optimization built on top of the pymoo framework. This application provides a comprehensive platform for defining, solving, and analyzing multi-objective optimization problems with support for static, dynamic, and many-objective scenarios.

## Features

### 🎯 Problem Definition

- **Arbitrary Variables**: Define continuous, integer, binary, and mixed-variable problems
- **Multiple Objectives**: Support for 2 to many objectives with minimize/maximize directions
- **Flexible Constraints**: Inequality and equality constraints with time-dependent formulations
- **Dynamic Problems**: Time-varying objectives and constraints for dynamic optimization

### 🧬 Algorithm Support

- **NSGA-II**: Fast non-dominated sorting with crowding distance
- **NSGA-III**: Reference point-based selection for many-objective problems
- **MOEA/D**: Decomposition-based multi-objective optimization
- **RM-MEDA**: Regularity model-based evolutionary algorithm
- **MOPSO**: Multi-objective particle swarm optimization

### 🔧 Advanced Configuration

- **Full Parameter Control**: Population size, generations, crossover/mutation parameters
- **Many-Objective Extensions**: MaNSGA-II with cone dominance and tunable parameter α
- **Dynamic Optimization**: ISVM prediction with POSMOTE reinitialization
- **Automatic Operators**: Variable type-based operator selection

### 📊 Real-time Visualization

- **Interactive Plots**: 2D/3D Pareto fronts with clickable solution inspection
- **Parallel Coordinates**: High-dimensional objective visualization
- **Convergence Monitoring**: Real-time metrics (HV, IGD, MIGD, MHV)
- **Population Evolution**: Animated visualization of optimization progress

### 🎛️ Decision Support

- **Preference Articulation**: Objective weighting, aspiration levels, reference points
- **Solution Ranking**: TOPSIS, weighted sum, compromise programming
- **Trade-off Analysis**: Comparative analysis between solutions
- **Interactive Exploration**: Click-to-inspect solution details

### 💾 Experiment Management

- **Save/Load**: Complete experiment persistence in JSON/YAML formats
- **Export Options**: CSV, JSON, images, PDF reports, Python code generation
- **Reproducibility**: Generate pymoo-compatible code for experiments
- **Benchmarking**: Compare multiple algorithm configurations

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Setup

1. **Clone the repository**:

```bash
git clone <repository-url>
cd multi-objective-optimization-gui
```

1. **Install dependencies**:

```bash
pip install -r requirements.txt
```

1. **Run the application**:

```bash
python main.py
```

1. **Access the GUI**:
Open your web browser and navigate to `http://localhost:8080`

### Development Setup

For development with hot reload:

```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
python main.py
```

## Usage Guide

### 1. Problem Definition

**Define Variables**:

- Click "Add Variable" to create decision variables
- Specify name, type (continuous/integer/binary), and bounds
- Set initial values (optional)

**Define Objectives**:

- Add at least 2 objectives for multi-objective optimization
- Choose minimize or maximize direction
- Write Python expressions using variable array `x`
- Enable time-dependent formulations for dynamic problems

**Define Constraints** (optional):

- Add inequality (≤ 0) or equality (= 0) constraints
- Use Python expressions with mathematical functions
- Support for time-dependent constraints

### 2. Algorithm Configuration

**Select Algorithm**:

- Choose from NSGA-II, NSGA-III, MOEA/D, RM-MEDA, or MOPSO
- Configure population size and maximum generations
- Set random seed for reproducibility

**Tune Parameters**:

- **NSGA-II**: Sampling strategy, tournament pressure, SBX crossover, polynomial mutation
- **NSGA-III**: Reference directions, partitions
- **MOEA/D**: Decomposition method, neighborhood size

**Many-Objective Options**:

- Enable MaNSGA-II cone dominance
- Configure cone dominance parameter α
- Replace standard crowding distance

**Dynamic Optimization**:

- Enable change detection with threshold settings
- Configure ISVM prediction parameters
- Set up POSMOTE reinitialization

### 3. Run Optimization

1. Click "Run Optimization" to start the process
2. Monitor real-time progress in the visualization panel
3. View convergence metrics and population evolution
4. Use "Stop" button to halt optimization early

### 4. Analyze Results

**Visualization**:

- Switch between 2D/3D Pareto front plots
- Use parallel coordinates for many-objective problems
- Monitor convergence and diversity metrics
- Click on solutions to inspect details

**Decision Making**:

- Set objective weights and aspiration levels
- Apply ranking methods (TOPSIS, weighted sum, etc.)
- Perform trade-off analysis between solutions
- Export preferred solutions

**Export Results**:

- Save complete experiments in JSON/YAML format
- Export solutions to CSV
- Generate publication-ready plots
- Create reproducible Python code

## Example Problems

### Basic Bi-objective Problem (ZDT1)

```python
# Variables: x0, x1 ∈ [0, 1]
# Objectives:
f1 = x[0]
f2 = (1 + 9*sum(x[1:])/len(x[1:])) * (1 - sqrt(x[0]/(1 + 9*sum(x[1:])/len(x[1:]))))
```

### Constrained Problem

```python
# Variables: x0, x1 ∈ [-5, 5]
# Objectives:
f1 = x[0]**2 + x[1]**2
f2 = (x[0] - 2)**2 + (x[1] - 1)**2

# Constraint:
g1 = x[0]**2 + x[1]**2 - 1  # ≤ 0 (inside unit circle)
```

### Many-objective Problem (DTLZ2)

```python
# Variables: x0, x1, x2, x3, x4 ∈ [0, 1]
# Objectives (4 objectives):
f1 = (1 + g) * cos(x[0]*pi/2) * cos(x[1]*pi/2) * cos(x[2]*pi/2)
f2 = (1 + g) * cos(x[0]*pi/2) * cos(x[1]*pi/2) * sin(x[2]*pi/2)
f3 = (1 + g) * cos(x[0]*pi/2) * sin(x[1]*pi/2)
f4 = (1 + g) * sin(x[0]*pi/2)
# where g = sum((x[3:] - 0.5)**2)
```

## Architecture

### Core Components

- **State Manager**: Handles experiment persistence and validation
- **Optimization Engine**: Integrates with pymoo algorithms and manages execution
- **Layout System**: Modular UI components for different sections
- **Callback System**: Handles user interactions and real-time updates

### File Structure

```
gui/
├── core/
│   ├── state_manager.py      # Experiment state management
│   └── optimization_engine.py # Pymoo integration
├── layouts/
│   ├── main_layout.py        # Main application layout
│   ├── problem_definition.py # Problem setup interface
│   ├── algorithm_config.py   # Algorithm configuration
│   ├── visualization.py      # Real-time plotting
│   └── results.py           # Results analysis and export
├── callbacks/
│   ├── navigation_callbacks.py    # Page navigation
│   ├── problem_callbacks.py       # Problem definition logic
│   ├── algorithm_callbacks.py     # Algorithm configuration
│   ├── visualization_callbacks.py # Plotting and monitoring
│   ├── results_callbacks.py       # Results processing
│   └── optimization_callbacks.py  # Optimization control
└── app.py                   # Main application factory
```

## Advanced Features

### Dynamic Optimization

- **Change Detection**: Automatic detection of environmental changes
- **ISVM Prediction**: Incremental Support Vector Machine for solution prediction
- **POSMOTE**: SMOTE applied to Pareto-optimal solutions for reinitialization

### Many-Objective Optimization

- **Cone Dominance**: MaNSGA-II implementation with tunable parameter α
- **Reference Points**: NSGA-III with customizable reference directions
- **Visualization**: Parallel coordinates for high-dimensional objectives

### Performance Metrics

- **Hypervolume (HV)**: Volume dominated by Pareto front
- **Inverted Generational Distance (IGD)**: Distance to reference front
- **Modified IGD (MIGD)**: For dynamic problems
- **Mean Hypervolume (MHV)**: Average hypervolume over time

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this software in your research, please cite:

```bibtex
@software{moo_gui,
  title={Multi-Objective Optimization GUI: A Research-Grade Interface for Pymoo},
  author={Your Name},
  year={2024},
  url={https://github.com/your-username/moo-gui}
}
```

## Acknowledgments

- Built on top of the excellent [pymoo](https://pymoo.org/) framework
- Inspired by Kalyanmoy Deb's multi-objective optimization principles
- UI components powered by [Dash](https://dash.plotly.com/) and [Plotly](https://plotly.com/)

## Support

For questions, bug reports, or feature requests, please open an issue on GitHub or contact the development team.

---

**Happy Optimizing! 🚀**
