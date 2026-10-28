#!/usr/bin/env python3
"""
Engineering optimization problem examples and templates.
Provides common engineering problems for testing and demonstration.
"""

from typing import Dict, Any, List


class EngineeringProblems:
    """Collection of common engineering optimization problems."""

    @staticmethod
    def welded_beam_design() -> Dict[str, Any]:
        """
        Welded beam design problem (4 variables, 2 objectives, 4 constraints).

        Variables:
            x[0]: Weld thickness (h)
            x[1]: Clamped bar length (l)
            x[2]: Height of the bar (t)
            x[3]: Thickness of the bar (b)

        Objectives:
            f1: Minimize cost
            f2: Minimize deflection

        Constraints:
            g1: Shear stress <= allowable
            g2: Normal stress <= allowable
            g3: Buckling load constraint
            g4: Deflection constraint
        """
        return {
            'name': 'Welded Beam Design',
            'description': 'Classic 4-variable welded beam structural design problem.',
            'variables': [
                {'name': 'h', 'type': 'continuous', 'lower': 0.125, 'upper': 5.0},
                {'name': 'l', 'type': 'continuous', 'lower': 0.1,   'upper': 10.0},
                {'name': 't', 'type': 'continuous', 'lower': 0.1,   'upper': 10.0},
                {'name': 'b', 'type': 'continuous', 'lower': 0.125, 'upper': 5.0},
            ],
            'objectives': [
                {
                    'name': 'Cost',
                    'direction': 'minimize',
                    'expression': '1.10471*x[0]**2*x[1] + 0.04811*x[2]*x[3]*(14.0 + x[1])',
                },
                {
                    'name': 'Deflection',
                    'direction': 'minimize',
                    'expression': (
                        '2.1952 / (x[3] * x[2]**3)'
                    ),
                },
            ],
            'constraints': [
                # Shear stress constraint  tau <= 13600  => tau - 13600 <= 0
                {
                    'name': 'shear_stress',
                    'expression': (
                        '((6000.0 / (sqrt(2) * x[0] * x[1]))**2 '
                        '+ (6000.0 * (14.0 + 0.5*x[1]) * sqrt(0.25*(x[1]**2 + (x[0]+x[2])**2)) '
                        '   / (2 * (0.707*x[0]*x[1] * (x[1]**2/12.0 + 0.25*(x[0]+x[2])**2))))**2 '
                        '+ (x[1] * 6000.0 * (14.0 + 0.5*x[1]) * sqrt(0.25*(x[1]**2 + (x[0]+x[2])**2)) '
                        '   / (0.707*x[0]*x[1] * (x[1]**2/12.0 + 0.25*(x[0]+x[2])**2))))**0.5 - 13600.0'
                    ),
                },
                # Normal bending stress  sigma <= 30000  => sigma - 30000 <= 0
                {
                    'name': 'bending_stress',
                    'expression': (
                        '504000.0 / (x[2]**2 * x[3]) - 30000.0'
                    ),
                },
                # Buckling load  Pc >= P=6000  => 6000 - Pc <= 0
                {
                    'name': 'buckling_load',
                    'expression': (
                        '6000.0 - (64746.022 * (1 - 0.0282346*x[2]) * x[2] * x[3]**3)'
                    ),
                },
                # Deflection constraint  delta <= 0.25  => delta - 0.25 <= 0
                {
                    'name': 'deflection_limit',
                    'expression': (
                        '2.1952 / (x[3] * x[2]**3) - 0.25'
                    ),
                },
            ],
        }

    @staticmethod
    def pressure_vessel_design() -> Dict[str, Any]:
        """
        Pressure vessel design problem (4 variables, 2 objectives, 4 constraints).

        Variables:
            x[0]: Thickness of shell (Ts)
            x[1]: Thickness of head (Th)
            x[2]: Inner radius (R)
            x[3]: Length of cylindrical section (L)

        Objectives:
            f1: Minimize total cost
            f2: Minimize weight
        """
        return {
            'name': 'Pressure Vessel Design',
            'description': 'Classic 4-variable pressure vessel design problem.',
            'variables': [
                {'name': 'Ts', 'type': 'continuous', 'lower': 0.0625, 'upper': 6.1875},
                {'name': 'Th', 'type': 'continuous', 'lower': 0.0625, 'upper': 6.1875},
                {'name': 'R',  'type': 'continuous', 'lower': 10.0,   'upper': 200.0},
                {'name': 'L',  'type': 'continuous', 'lower': 10.0,   'upper': 200.0},
            ],
            'objectives': [
                {
                    'name': 'Cost',
                    'direction': 'minimize',
                    'expression': (
                        '0.6224*x[0]*x[2]*x[3] '
                        '+ 1.7781*x[1]*x[2]**2 '
                        '+ 3.1661*x[0]**2*x[3] '
                        '+ 19.84*x[0]**2*x[2]'
                    ),
                },
                {
                    'name': 'Weight',
                    'direction': 'minimize',
                    'expression': (
                        '(4.0/3.0)*pi*x[2]**3 '
                        '+ pi*x[2]**2*x[3]'
                    ),
                },
            ],
            'constraints': [
                {'name': 'c1', 'expression': '-x[0] + 0.0193*x[2]'},
                {'name': 'c2', 'expression': '-x[1] + 0.00954*x[2]'},
                {'name': 'c3', 'expression': (
                    '-pi*x[2]**2*x[3] - (4.0/3.0)*pi*x[2]**3 + 1296000.0'
                )},
                {'name': 'c4', 'expression': 'x[3] - 240.0'},
            ],
        }

    @staticmethod
    def get_problem(name: str) -> Dict[str, Any]:
        """Return a problem dict by name."""
        problems = {
            'welded_beam':      EngineeringProblems.welded_beam_design,
            'pressure_vessel':  EngineeringProblems.pressure_vessel_design,
        }
        factory = problems.get(name)
        if factory is None:
            raise ValueError(
                f"Unknown engineering problem '{name}'. "
                f"Available: {list(problems.keys())}"
            )
        return factory()

    @staticmethod
    def list_problems() -> List[str]:
        """Return names of all available engineering problems."""
        return ['welded_beam', 'pressure_vessel']
