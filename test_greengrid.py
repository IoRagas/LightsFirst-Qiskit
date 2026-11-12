"""
test_greengrid.py - Automated Unit & Integration Test Suite for GreenGrid AI
Verifies:
1. Grid simulation initialization and parameters.
2. Inviolable 100% protection of hospital and residential demand under all disasters.
3. Priority-aware and carbon-minimizing macro scheduler logic.
4. Qiskit QAOA Deficit QUBO formulation and exact classical baseline comparison.
"""

import unittest
from simulation import GridSimulation, Region, DataCenter
from scheduler import MacroScheduler, compare_scenarios
from quantum_solver import DeficitQUBOModel, QuantumQAOASolver
from classical_solver import ClassicalSolvers


class TestGreenGridAI(unittest.TestCase):

    def setUp(self):
        self.sim = GridSimulation(seed=42)
        self.scheduler = MacroScheduler(self.sim)

    def test_simulation_baseline(self):
        """Asserts all 4 regions are initialized with valid power balances."""
        self.assertEqual(len(self.sim.regions), 4)
        for r_id, reg in self.sim.regions.items():
            self.assertTrue(reg.is_active)
            self.assertGreater(reg.total_supply_mw, 0)
            self.assertGreater(reg.hospital_demand_mw, 0)
            # Available AI power must equal max(0, supply - critical - reserve)
            expected_ai = max(0.0, reg.total_supply_mw - reg.critical_demand_mw - reg.reserve_margin_mw)
            self.assertAlmostEqual(reg.available_ai_power_mw, expected_ai, places=2)

    def test_hospital_protection_under_flood(self):
        """Asserts hospital demands remain 100% shielded during a Guddu/Dadu flood."""
        self.sim.trigger_flood_dadu()
        rep = self.scheduler.optimize()
        self.assertEqual(rep.critical_load_protected_pct, 100.0)
        self.assertAlmostEqual(self.sim.regions["Karachi"].hospital_demand_mw, 20.0)
        self.assertAlmostEqual(self.sim.regions["Karachi"].residential_demand_mw, 25.0)

    def test_hospital_protection_under_heatwave(self):
        """Asserts hospital demands remain 100% shielded during a Karachi peak heatwave."""
        self.sim.trigger_heatwave_karachi()
        rep = self.scheduler.optimize()
        self.assertEqual(rep.critical_load_protected_pct, 100.0)
        self.assertAlmostEqual(self.sim.regions["Karachi"].hospital_demand_mw, 20.0)
        self.assertAlmostEqual(self.sim.regions["Karachi"].residential_demand_mw, 40.0)

    def test_hospital_protection_under_outage(self):
        """Asserts hospital demands remain 100% shielded during a Lahore grid trip."""
        self.sim.trigger_outage_lahore()
        rep = self.scheduler.optimize()
        self.assertEqual(rep.critical_load_protected_pct, 100.0)
        self.assertEqual(self.sim.regions["Lahore"].is_active, False)

    def test_macro_scheduler_allocation_validity(self):
        """Asserts scheduled workloads never exceed available regional power or GPUs."""
        rep = self.scheduler.optimize()
        budgets = self.scheduler.calculate_regional_budgets(self.sim)

        self.assertGreater(rep.scheduled_jobs, 0)
        self.assertGreater(rep.total_power_used_mw, 0)
        self.assertGreater(rep.total_co2_emissions_kg, 0)

        for r_id in self.sim.regions:
            used_power = rep.regional_power_used[r_id]
            used_gpu = rep.regional_gpu_used[r_id]
            avail_power = budgets[r_id]["available_power_mw"]
            avail_gpu = budgets[r_id]["available_gpus"]

            self.assertLessEqual(used_power, avail_power + 1e-4)
            self.assertLessEqual(used_gpu, avail_gpu)

    def test_quantum_deficit_qubo_formulation(self):
        """Asserts the Qiskit QuadraticProgram converts to a valid 8-qubit Ising Hamiltonian."""
        model = DeficitQUBOModel()
        self.assertEqual(model.qubo.get_num_binary_vars(), 8)
        self.assertGreater(len(model.operator), 0)
        self.assertIsNotNone(model.offset)

    def test_exact_vs_qaoa_solution(self):
        """Verifies QAOA converges and achieves an approximation ratio >= 0.85 on test instance."""
        model = DeficitQUBOModel()
        solver = QuantumQAOASolver(model, p_layers=1)
        res = solver.solve(max_iter=50, seed=42)

        self.assertIn("qaoa_energy", res)
        self.assertIn("approximation_ratio", res)
        self.assertGreaterEqual(res["approximation_ratio"], 0.85)
        self.assertEqual(len(res["best_bitstring"]), 8)
        self.assertIn("exact_baseline", res)
        self.assertEqual(res["exact_baseline"]["best_energy"], -24.90)


if __name__ == "__main__":
    unittest.main()
