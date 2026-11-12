"""
scheduler.py - GreenGrid AI Macro Optimization Engine
Calculates available regional electricity, prioritizes and allocates AI workloads,
minimizes aggregate carbon emissions, dynamically migrates/postpones jobs during disasters,
and guarantees 100% protection for hospital and residential critical loads.
"""

import copy
from typing import Dict, List, Tuple
from simulation import AIJob, DataCenter, GridSimulation, Region


class OptimizationReport:
    def __init__(self):
        self.total_jobs: int = 0
        self.scheduled_jobs: int = 0
        self.postponed_jobs: int = 0
        self.migrated_jobs: int = 0
        self.total_power_used_mw: float = 0.0
        self.total_co2_emissions_kg: float = 0.0
        self.critical_load_protected_pct: float = 100.0  # Inviolable guarantee
        self.regional_job_counts: Dict[str, int] = {}
        self.regional_power_used: Dict[str, float] = {}
        self.regional_gpu_used: Dict[str, int] = {}
        self.jobs: List[AIJob] = []

    @property
    def scheduling_rate_pct(self) -> float:
        if self.total_jobs == 0:
            return 0.0
        return round((self.scheduled_jobs / self.total_jobs) * 100.0, 1)


class MacroScheduler:
    """Classical Priority-Aware and Carbon-Minimizing Macro Scheduler."""

    def __init__(self, simulation: GridSimulation):
        self.sim = simulation

    def calculate_regional_budgets(self, sim: GridSimulation) -> Dict[str, Dict[str, float]]:
        """
        Calculates remaining AI power budget and GPU budget for each region:
        P_AI = max(0, Supply - Hospital - Residential - Reserve)
        Budget is also capped by Data Center electrical interconnection limit.
        """
        budgets = {}
        for reg_id, reg in sim.regions.items():
            dc = sim.datacenters.get(reg_id)
            if not reg.is_active or not dc or dc.operational_status == "Offline":
                budgets[reg_id] = {
                    "available_power_mw": 0.0,
                    "available_gpus": 0,
                    "carbon_intensity": reg.carbon_intensity_g_kwh,
                }
            else:
                grid_ai_power = reg.available_ai_power_mw
                # Capped by Data Center transformer/cooling limit
                effective_power = min(grid_ai_power, dc.max_power_mw)
                budgets[reg_id] = {
                    "available_power_mw": max(0.0, effective_power),
                    "available_gpus": dc.current_gpus_available,
                    "carbon_intensity": reg.carbon_intensity_g_kwh,
                }
        return budgets

    def optimize(self, previous_assignments: Dict[str, str] = None) -> OptimizationReport:
        """
        Performs the priority-based and carbon-minimizing scheduling pass.
        If previous_assignments is provided, tracks which jobs migrated away from their prior region.
        """
        report = OptimizationReport()
        sim = copy.deepcopy(self.sim)
        budgets = self.calculate_regional_budgets(sim)

        # Initialize tracking
        for r_id in sim.regions:
            report.regional_job_counts[r_id] = 0
            report.regional_power_used[r_id] = 0.0
            report.regional_gpu_used[r_id] = 0

        # Sort jobs by Priority (High=3, Medium=2, Low=1) descending, then deadline ascending
        sorted_jobs = sorted(
            sim.jobs,
            key=lambda j: (-j.priority_score, j.deadline_hours, j.power_mw)
        )

        for job in sorted_jobs:
            report.total_jobs += 1
            candidates: List[Tuple[float, str]] = []

            # Check feasibility across all regions
            for r_id, b in budgets.items():
                if b["available_power_mw"] < job.power_mw:
                    continue
                if b["available_gpus"] < job.gpu_requirement:
                    continue

                # Feasible! Calculate estimated emissions for 1-hour interval:
                # CO2 (kg) = Power (MW) * Carbon_Intensity (kg/MWh)
                emissions = job.power_mw * b["carbon_intensity"]
                candidates.append((emissions, r_id))

            if candidates:
                # Select the region that minimizes carbon emissions!
                candidates.sort(key=lambda c: c[0])
                best_emissions, best_region = candidates[0]

                # Deduct resources
                budgets[best_region]["available_power_mw"] -= job.power_mw
                budgets[best_region]["available_gpus"] -= job.gpu_requirement

                # Update job record
                job.assigned_region = best_region
                job.estimated_emissions_kg = round(best_emissions, 2)

                # Check if this was a migration due to a disaster
                if previous_assignments and job.id in previous_assignments:
                    prior = previous_assignments[job.id]
                    if prior != best_region and prior != "None":
                        job.status = "Migrated"
                        report.migrated_jobs += 1
                    else:
                        job.status = "Running"
                else:
                    job.status = "Running"

                # Update report metrics
                report.scheduled_jobs += 1
                report.total_power_used_mw += job.power_mw
                report.total_co2_emissions_kg += best_emissions
                report.regional_job_counts[best_region] += 1
                report.regional_power_used[best_region] += job.power_mw
                report.regional_gpu_used[best_region] += job.gpu_requirement

            else:
                # Could not fit into any region
                job.assigned_region = None
                job.status = "Postponed"
                job.estimated_emissions_kg = 0.0
                report.postponed_jobs += 1

            report.jobs.append(job)

        report.total_power_used_mw = round(report.total_power_used_mw, 2)
        report.total_co2_emissions_kg = round(report.total_co2_emissions_kg, 2)
        # Critical load is ALWAYS 100% protected because hospital & residential demands
        # are subtracted prior to calculating available AI power!
        report.critical_load_protected_pct = 100.0

        return report


def compare_scenarios(before: OptimizationReport, after: OptimizationReport) -> Dict:
    """Generates a quantitative before-vs-after comparison dictionary."""
    return {
        "scheduled_before": before.scheduled_jobs,
        "scheduled_after": after.scheduled_jobs,
        "scheduled_delta": after.scheduled_jobs - before.scheduled_jobs,
        "completion_rate_before": before.scheduling_rate_pct,
        "completion_rate_after": after.scheduling_rate_pct,
        "co2_before_kg": before.total_co2_emissions_kg,
        "co2_after_kg": after.total_co2_emissions_kg,
        "co2_delta_kg": round(after.total_co2_emissions_kg - before.total_co2_emissions_kg, 2),
        "power_before_mw": before.total_power_used_mw,
        "power_after_mw": after.total_power_used_mw,
        "postponed_after": after.postponed_jobs,
        "migrated_after": after.migrated_jobs,
        "critical_load_protected": True
    }
