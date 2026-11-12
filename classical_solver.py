"""
classical_solver.py - Exact Ground-Truth & Heuristic Classical Baselines
Provides:
1. Exact Exhaustive State Enumerator (evaluates all 2^N states to prove mathematical ground truth).
2. Classical Simulated Annealing Solver (standard optimization metaheuristic).
3. Greedy Priority Dispatch Heuristic.
"""

import math
import random
import time
from typing import Dict, List, Tuple
import numpy as np


class ClassicalSolvers:
    """Implements classical baseline optimization solvers for QUBO/Ising problems."""

    @staticmethod
    def evaluate_qubo_energy(x: np.ndarray, Q_matrix: np.ndarray, linear_coeffs: np.ndarray, offset: float) -> float:
        """Computes E(x) = x^T Q x + c^T x + offset"""
        quad = float(x @ Q_matrix @ x)
        lin = float(linear_coeffs @ x)
        return quad + lin + offset

    @classmethod
    def solve_exact_brute_force(
        cls, Q_matrix: np.ndarray, linear_coeffs: np.ndarray, offset: float
    ) -> Dict:
        """
        Exhaustively iterates over all 2^N binary states to find the mathematically guaranteed
        global minimum energy and optimal bitstring.
        """
        start_time = time.perf_counter()
        n = len(linear_coeffs)
        total_states = 1 << n

        best_energy = float("inf")
        best_bitstring = None
        all_energies = []

        for i in range(total_states):
            # Convert integer to binary array of length n
            bitstring = [(i >> k) & 1 for k in range(n)]
            x = np.array(bitstring, dtype=float)
            energy = cls.evaluate_qubo_energy(x, Q_matrix, linear_coeffs, offset)
            all_energies.append(energy)

            if energy < best_energy:
                best_energy = energy
                best_bitstring = bitstring

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "solver": "Exact Brute-Force (Ground Truth)",
            "best_energy": round(best_energy, 4),
            "best_bitstring": "".join(str(b) for b in best_bitstring),
            "best_x": best_bitstring,
            "total_states_evaluated": total_states,
            "runtime_ms": round(elapsed_ms, 2),
            "all_energies": all_energies,
        }

    @classmethod
    def solve_simulated_annealing(
        cls,
        Q_matrix: np.ndarray,
        linear_coeffs: np.ndarray,
        offset: float,
        initial_temp: float = 100.0,
        cooling_rate: float = 0.95,
        num_iterations: int = 500,
        seed: int = 42
    ) -> Dict:
        """
        Simulated Annealing metaheuristic: stochastic search with Metropolis acceptance.
        """
        random.seed(seed)
        np.random.seed(seed)
        start_time = time.perf_counter()
        n = len(linear_coeffs)

        # Initial random state
        current_x = np.random.randint(0, 2, size=n).astype(float)
        current_energy = cls.evaluate_qubo_energy(current_x, Q_matrix, linear_coeffs, offset)

        best_x = current_x.copy()
        best_energy = current_energy
        temp = initial_temp
        trajectory = [current_energy]

        for step in range(num_iterations):
            # Propose flipping one random bit
            flip_idx = random.randint(0, n - 1)
            candidate_x = current_x.copy()
            candidate_x[flip_idx] = 1.0 - candidate_x[flip_idx]

            candidate_energy = cls.evaluate_qubo_energy(candidate_x, Q_matrix, linear_coeffs, offset)
            delta_e = candidate_energy - current_energy

            if delta_e < 0 or random.random() < math.exp(-delta_e / max(temp, 1e-6)):
                current_x = candidate_x
                current_energy = candidate_energy
                if current_energy < best_energy:
                    best_energy = current_energy
                    best_x = current_x.copy()

            temp *= cooling_rate
            trajectory.append(best_energy)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "solver": "Classical Simulated Annealing",
            "best_energy": round(best_energy, 4),
            "best_bitstring": "".join(str(int(b)) for b in best_x),
            "best_x": [int(b) for b in best_x],
            "runtime_ms": round(elapsed_ms, 2),
            "trajectory": trajectory,
        }
