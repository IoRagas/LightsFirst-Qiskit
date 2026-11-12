"""
benchmarking.py - Rigorous Evaluation Engine & Comparative Benchmarks
Generates quantitative comparisons:
1. Macro Grid Performance: Normal vs Flood vs Heatwave vs Outage.
2. Quantum vs Classical Baseline: Exact Brute-Force vs Simulated Annealing vs Qiskit QAOA.
3. Publication-grade figures saved to disk for inclusion in report and presentations.
"""

import json
import time
from typing import Dict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from simulation import GridSimulation
from scheduler import MacroScheduler, compare_scenarios
from quantum_solver import DeficitQUBOModel, QuantumQAOASolver


def run_macro_grid_benchmarks() -> Dict:
    """Evaluates the macro grid across all 4 operational states."""
    sim = GridSimulation(seed=42)
    scheduler = MacroScheduler(sim)

    # 1. Baseline Normal
    normal_rep = scheduler.optimize()
    normal_assignments = {j.id: j.assigned_region for j in normal_rep.jobs}

    # 2. Karachi Peak Heatwave
    sim.trigger_heatwave_karachi()
    heatwave_rep = scheduler.optimize(previous_assignments=normal_assignments)
    heatwave_comp = compare_scenarios(normal_rep, heatwave_rep)

    # 3. Guddu / Dadu Flood
    sim.trigger_flood_dadu()
    flood_rep = scheduler.optimize(previous_assignments=normal_assignments)
    flood_comp = compare_scenarios(normal_rep, flood_rep)

    # 4. Lahore 500kV Outage
    sim.trigger_outage_lahore()
    outage_rep = scheduler.optimize(previous_assignments=normal_assignments)
    outage_comp = compare_scenarios(normal_rep, outage_rep)

    return {
        "normal": normal_rep,
        "flood": flood_rep,
        "flood_comparison": flood_comp,
        "heatwave": heatwave_rep,
        "heatwave_comparison": heatwave_comp,
        "outage": outage_rep,
        "outage_comparison": outage_comp,
    }


def run_quantum_benchmarks() -> Dict:
    """Runs the side-by-side evaluation of Qiskit QAOA vs Exact Ground Truth vs Simulated Annealing."""
    model = DeficitQUBOModel()
    solver = QuantumQAOASolver(model, p_layers=2)
    results = solver.solve(max_iter=80)
    return results


def generate_benchmark_plots(macro_results: Dict, quantum_results: Dict):
    """Renders and saves high-resolution publication-quality figures."""
    plt.style.use('default')
    plt.rcParams['figure.facecolor'] = '#FFFFFF'
    plt.rcParams['axes.facecolor'] = '#FFFFFF'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
    plt.rcParams['axes.edgecolor'] = '#CBD5E1'
    plt.rcParams['grid.color'] = '#E2E8F0'

    # Figure 1: Macro Grid Workload Completion & Disruption Impact
    fig, ax1 = plt.subplots(figsize=(8.5, 4.5), dpi=300)
    scenarios = ["Normal Grid", "Karachi Heatwave", "Guddu Flood", "Lahore Trip"]
    scheduled = [
        macro_results["normal"].scheduled_jobs,
        macro_results["heatwave"].scheduled_jobs,
        macro_results["flood"].scheduled_jobs,
        macro_results["outage"].scheduled_jobs,
    ]
    postponed = [
        macro_results["normal"].postponed_jobs,
        macro_results["heatwave"].postponed_jobs,
        macro_results["flood"].postponed_jobs,
        macro_results["outage"].postponed_jobs,
    ]

    x = np.arange(len(scenarios))
    width = 0.35

    rects1 = ax1.bar(x - width/2, scheduled, width, label='Scheduled Workloads', color='#059669')
    rects2 = ax1.bar(x + width/2, postponed, width, label='Postponed Workloads (Step Aside)', color='#E11D48')

    ax1.set_ylabel('Number of AI Jobs', fontsize=11, fontweight='bold', color='#0F172A')
    ax1.set_title('Lights First: AI Workload Step-Aside & 100% Hospital Shield Across Disasters', fontsize=12, fontweight='bold', pad=12, color='#0F172A')
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios, fontsize=10, fontweight='bold', color='#1E293B')
    ax1.tick_params(colors='#334155')
    ax1.legend(loc='upper right', frameon=True, facecolor='#F8FAFC', edgecolor='#CBD5E1')
    ax1.grid(True, linestyle='--', alpha=0.7)

    # Label bars
    for rect in rects1:
        h = rect.get_height()
        ax1.annotate(f'{h}', xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                    textcoords="offset points", ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#065F46')
    for rect in rects2:
        h = rect.get_height()
        ax1.annotate(f'{h}', xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                    textcoords="offset points", ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#9F1239')

    plt.tight_layout()
    plt.savefig("disaster_workload_comparison.png", dpi=300)
    plt.close()

    # Figure 2: Quantum QAOA Parameter Optimization Convergence
    history = quantum_results.get("convergence_history", [])
    if history:
        fig, ax = plt.subplots(figsize=(7, 4), dpi=300)
        ax.plot(range(1, len(history) + 1), history, marker='o', markersize=3.5, color='#0284C7', linewidth=2.0, label='QAOA <H(γ, β)>')
        exact_e = quantum_results["exact_baseline"]["best_energy"]
        ax.axhline(exact_e, color='#E11D48', linestyle='--', linewidth=1.6, label=f'Exact Ground Truth ({exact_e:.2f})')
        ax.set_xlabel('COBYLA Classical Optimizer Iterations', fontsize=10, fontweight='bold', color='#0F172A')
        ax.set_ylabel('Expectation Energy (Arbitrary Units)', fontsize=10, fontweight='bold', color='#0F172A')
        ax.set_title('Qiskit QAOA Convergence Trajectory (8-Qubit Deficit QUBO, p=2)', fontsize=11, fontweight='bold', pad=10, color='#0F172A')
        ax.tick_params(colors='#334155')
        ax.legend(frameon=True, facecolor='#F8FAFC', edgecolor='#CBD5E1')
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig("qaoa_convergence.png", dpi=300)
        plt.close()

    # Figure 3: Solver Comparison (Exact vs SA vs QAOA)
    fig, (ax_e, ax_t) = plt.subplots(1, 2, figsize=(9, 4), dpi=300)
    solvers = ["Exact Brute-Force", "Simulated Annealing", "Qiskit QAOA (p=2)"]
    energies = [
        quantum_results["exact_baseline"]["best_energy"],
        quantum_results["sa_baseline"]["best_energy"],
        quantum_results["best_sampled_energy"],
    ]
    runtimes = [
        quantum_results["exact_baseline"]["runtime_ms"],
        quantum_results["sa_baseline"]["runtime_ms"],
        quantum_results["runtime_ms"],
    ]

    colors = ['#059669', '#D97706', '#0284C7']
    ax_e.bar(solvers, energies, color=colors, width=0.52)
    ax_e.set_title('Objective Energy (Lower is Better)', fontsize=10, fontweight='bold', color='#0F172A')
    ax_e.set_ylabel('Energy', fontsize=10, color='#0F172A')
    ax_e.tick_params(axis='x', rotation=15, colors='#334155')
    ax_e.grid(True, linestyle='--', alpha=0.7)

    ax_t.bar(solvers, runtimes, color=colors, width=0.52)
    ax_t.set_title('Solver Execution Latency (ms)', fontsize=10, fontweight='bold', color='#0F172A')
    ax_t.set_ylabel('Milliseconds (ms)', fontsize=10, color='#0F172A')
    ax_t.tick_params(axis='x', rotation=15, colors='#334155')
    ax_t.grid(True, linestyle='--', alpha=0.7)

    plt.suptitle('Optimization Benchmark: Classical Ground Truth vs. NISQ Qiskit QAOA', fontsize=11, fontweight='bold', color='#0F172A')
    plt.tight_layout()
    plt.savefig("quantum_vs_classical_benchmark.png", dpi=300)
    plt.close()
    print("Benchmark plots successfully generated and saved!")


if __name__ == "__main__":
    print("Running Macro Grid Benchmarks...")
    macro_res = run_macro_grid_benchmarks()
    print("Running Qiskit QAOA Benchmarks...")
    quantum_res = run_quantum_benchmarks()
    print("Generating Figures...")
    generate_benchmark_plots(macro_res, quantum_res)
    print("All benchmarks completed successfully!")
