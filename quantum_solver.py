"""
quantum_solver.py - Qiskit 2.x QAOA Quantum Core for Deficit Workload Allocation
Formulates the high-stakes disaster power-deficit allocation problem as a QuadraticProgram,
maps it to an Ising Hamiltonian, and solves it using the Quantum Approximate Optimization Algorithm (QAOA)
with statevector simulation and COBYLA parameter optimization.
"""

import time
from typing import Dict, List, Tuple
import numpy as np
from scipy.optimize import minimize

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.converters import QuadraticProgramToQubo

from classical_solver import ClassicalSolvers


class DeficitQUBOModel:
    """
    Defines the high-stakes critical workload allocation problem when a disaster
    restricts green electricity capacity.
    """

    def __init__(
        self,
        job_names: List[str] = None,
        priority_weights: List[float] = None,
        power_demands_mw: List[float] = None,
        carbon_penalties: List[float] = None,
        max_power_budget_mw: float = 5.0,
        penalty_multiplier: float = 12.0
    ):
        if job_names is None:
            self.job_names = [
                "ICU Diagnostic Vision #1",
                "Wildfire Plume Tracker #2",
                "Mesh Comms Telematics #3",
                "Grid Stability Predictor #4",
            ]
            self.priority_weights = [15.0, 12.0, 10.0, 8.0]
            self.power_demands_mw = [2.0, 2.5, 1.5, 3.0]
            self.carbon_penalties = [0.9, 1.2, 0.6, 1.5]
        else:
            self.job_names = job_names
            self.priority_weights = priority_weights
            self.power_demands_mw = power_demands_mw
            self.carbon_penalties = carbon_penalties

        self.max_power_budget_mw = max_power_budget_mw
        self.penalty_multiplier = penalty_multiplier
        self.num_jobs = len(self.job_names)

        # Build Qiskit QuadraticProgram
        self.qp = self._build_quadratic_program()
        self.conv = QuadraticProgramToQubo(penalty=self.penalty_multiplier)
        self.qubo = self.conv.convert(self.qp)
        self.operator, self.offset = self.qubo.to_ising()

        # Extract Q-matrix and linear terms for exact classical baseline
        self.Q_matrix, self.linear_coeffs, self.qubo_offset = self._extract_qubo_matrices()

    def _build_quadratic_program(self) -> QuadraticProgram:
        """Constructs the constrained optimization model with integer-scaled coefficients."""
        qp = QuadraticProgram(name="Disaster_Deficit_Allocation")
        for i in range(self.num_jobs):
            qp.binary_var(name=f"x_{i}")

        # Objective: Maximize net utility: sum (priority - carbon) * x_i
        # In minimization form: minimize sum -(priority - carbon) * x_i
        linear_objective = {}
        for i in range(self.num_jobs):
            net_benefit = self.priority_weights[i] - self.carbon_penalties[i]
            linear_objective[f"x_{i}"] = -net_benefit

        qp.minimize(linear=linear_objective)

        # Scale float MW power values to exact integers (e.g. 2.5 MW -> 5, 5.0 MW -> 10)
        # to satisfy Qiskit's exact discrete slack variable conversion
        scale = 2
        power_constraint_int = {f"x_{i}": int(round(self.power_demands_mw[i] * scale)) for i in range(self.num_jobs)}
        max_power_budget_int = int(round(self.max_power_budget_mw * scale))

        qp.linear_constraint(
            linear=power_constraint_int,
            sense="<=",
            rhs=max_power_budget_int,
            name="power_budget_constraint"
        )
        return qp

    def _extract_qubo_matrices(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """Extracts numerical matrix Q, linear vector c, and scalar offset from QUBO."""
        n = self.qubo.get_num_binary_vars()
        Q = np.zeros((n, n))
        linear = np.zeros(n)

        # Quadratic terms
        for (i, j), coeff in self.qubo.objective.quadratic.to_dict().items():
            idx_i = int(i) if isinstance(i, (int, np.integer)) else self.qubo.variables_index[i]
            idx_j = int(j) if isinstance(j, (int, np.integer)) else self.qubo.variables_index[j]
            Q[idx_i, idx_j] += float(coeff)

        # Linear terms
        for i, coeff in self.qubo.objective.linear.to_dict().items():
            idx_i = int(i) if isinstance(i, (int, np.integer)) else self.qubo.variables_index[i]
            linear[idx_i] = float(coeff)

        offset = float(self.qubo.objective.constant)
        return Q, linear, offset


class QuantumQAOASolver:
    """
    Implements QAOA with modern Qiskit 2.x parameterized circuits,
    Statevector expectation valuation, and COBYLA classical optimization.
    """

    def __init__(self, model: DeficitQUBOModel, p_layers: int = 2):
        self.model = model
        self.p_layers = p_layers
        self.n_qubits = model.qubo.get_num_binary_vars()
        self.ising_op = model.operator
        self.offset = model.offset
        self.history_energies = []

    def build_qaoa_circuit(self, gamma: List[float], beta: List[float]) -> QuantumCircuit:
        """Constructs the p-layer QAOA quantum circuit."""
        qc = QuantumCircuit(self.n_qubits)
        # Uniform superposition
        qc.h(range(self.n_qubits))

        # Loop over QAOA layers
        for layer in range(self.p_layers):
            g = gamma[layer]
            b = beta[layer]

            # Phase Separator Unitary: exp(-i * gamma * H_C)
            for pauli_term, coeff in zip(self.ising_op.paulis, self.ising_op.coeffs):
                weight = float(np.real(coeff))
                z_indices = [idx for idx, p in enumerate(reversed(str(pauli_term))) if p == 'Z']

                if len(z_indices) == 1:
                    # Single qubit Z rotation: Rz(2 * gamma * weight)
                    qc.rz(2.0 * g * weight, z_indices[0])
                elif len(z_indices) == 2:
                    # Two-qubit ZZ interaction: CX -> Rz -> CX
                    q0, q1 = z_indices[0], z_indices[1]
                    qc.cx(q0, q1)
                    qc.rz(2.0 * g * weight, q1)
                    qc.cx(q0, q1)

            # Mixer Unitary: exp(-i * beta * H_M) = Rx(2 * beta)
            for q in range(self.n_qubits):
                qc.rx(2.0 * b, q)

        return qc

    def compute_energy(self, params: np.ndarray) -> float:
        """Evaluates expectation value <psi| H |psi> + offset."""
        gamma = params[:self.p_layers]
        beta = params[self.p_layers:]

        qc = self.build_qaoa_circuit(gamma, beta)
        sv = Statevector.from_instruction(qc)
        exp_val = float(np.real(sv.expectation_value(self.ising_op)))
        total_energy = exp_val + self.offset
        self.history_energies.append(total_energy)
        return total_energy

    def solve(self, max_iter: int = 80, seed: int = 42) -> Dict:
        """Executes the classical-quantum hybrid optimization loop."""
        start_time = time.perf_counter()
        np.random.seed(seed)
        self.history_energies = []

        # Scanned initial parameter angles for stable convergence
        init_gamma = [0.35, 0.20][:self.p_layers]
        init_beta = [0.65, 0.40][:self.p_layers]
        while len(init_gamma) < self.p_layers:
            init_gamma.append(0.2)
            init_beta.append(0.3)
        init_params = np.array(init_gamma + init_beta)

        opt_res = minimize(
            self.compute_energy,
            init_params,
            method="COBYLA",
            options={"maxiter": max_iter, "disp": False}
        )

        opt_params = opt_res.x
        optimal_gamma = opt_params[:self.p_layers]
        optimal_beta = opt_params[self.p_layers:]

        # Optimal circuit and statevector
        optimal_qc = self.build_qaoa_circuit(optimal_gamma, optimal_beta)
        optimal_sv = Statevector.from_instruction(optimal_qc)
        probs = optimal_sv.probabilities_dict()

        # Find bitstring with maximum probability among sampled states
        # In Qiskit, bitstring is little-endian (qubit n-1 to qubit 0); reverse to match var indices
        standard_probs = {k[::-1]: v for k, v in probs.items()}
        sorted_sampled_states = sorted(standard_probs.items(), key=lambda item: item[1], reverse=True)

        # Evaluate real-world energy for top states
        best_measured_state = None
        best_measured_energy = float("inf")
        best_decision_bits = None

        for bitstring, prob in sorted_sampled_states[:12]:
            x_vec = np.array([int(b) for b in bitstring], dtype=float)
            e_val = ClassicalSolvers.evaluate_qubo_energy(
                x_vec, self.model.Q_matrix, self.model.linear_coeffs, self.model.qubo_offset
            )
            # Check feasibility on power budget
            consumed_mw = sum(self.model.power_demands_mw[i] * x_vec[i] for i in range(self.model.num_jobs))
            if consumed_mw <= self.model.max_power_budget_mw:
                if e_val < best_measured_energy:
                    best_measured_energy = e_val
                    best_measured_state = bitstring
                    best_decision_bits = bitstring[:self.model.num_jobs]

        # Fallback if no feasible in top 12
        if best_measured_state is None:
            best_measured_state = sorted_sampled_states[0][0]
            best_decision_bits = best_measured_state[:self.model.num_jobs]
            x_vec = np.array([int(b) for b in best_measured_state], dtype=float)
            best_measured_energy = ClassicalSolvers.evaluate_qubo_energy(
                x_vec, self.model.Q_matrix, self.model.linear_coeffs, self.model.qubo_offset
            )

        top_bitstring = sorted_sampled_states[0][0]
        top_prob = sorted_sampled_states[0][1]

        qaoa_exp_energy = float(opt_res.fun)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        circuit_depth = optimal_qc.depth()
        cx_count = optimal_qc.count_ops().get("cx", 0)

        # Baseline comparison
        exact_result = ClassicalSolvers.solve_exact_brute_force(
            self.model.Q_matrix, self.model.linear_coeffs, self.model.qubo_offset
        )
        sa_result = ClassicalSolvers.solve_simulated_annealing(
            self.model.Q_matrix, self.model.linear_coeffs, self.model.qubo_offset
        )

        e_min = exact_result["best_energy"]
        e_max = max(exact_result["all_energies"]) if exact_result.get("all_energies") else e_min + 1.0

        # Approximation ratio based on best feasible measured quantum sample
        denom = e_max - e_min
        if denom > 1e-6:
            approx_ratio = max(0.0, min(1.0, (e_max - best_measured_energy) / denom))
        else:
            approx_ratio = 1.0

        # Selected jobs based on quantum decision variables
        selected_jobs = []
        for i, bit in enumerate(best_decision_bits):
            if bit == '1':
                selected_jobs.append(self.model.job_names[i])

        return {
            "solver": f"Qiskit QAOA (p={self.p_layers})",
            "qaoa_energy": round(qaoa_exp_energy, 4),
            "best_sampled_energy": round(best_measured_energy, 4),
            "best_bitstring": best_measured_state,
            "decision_bitstring": best_decision_bits,
            "max_probability": round(top_prob, 4),
            "ground_state_probability": round(standard_probs.get(exact_result["best_bitstring"], 0.0), 4),
            "approximation_ratio": round(approx_ratio, 4),
            "circuit_depth": circuit_depth,
            "cx_count": cx_count,
            "n_qubits": self.n_qubits,
            "runtime_ms": round(elapsed_ms, 2),
            "convergence_history": self.history_energies,
            "optimal_gamma": [round(float(g), 4) for g in optimal_gamma],
            "optimal_beta": [round(float(b), 4) for b in optimal_beta],
            "exact_baseline": exact_result,
            "sa_baseline": sa_result,
            "selected_jobs": selected_jobs,
            "state_probabilities": {k: round(v, 4) for k, v in standard_probs.items() if v > 0.01}
        }
