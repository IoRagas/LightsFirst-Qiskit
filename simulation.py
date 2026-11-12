"""
simulation.py - Lights First Simulation Engine
Models geographical electricity regions across Pakistan (Karachi, Lahore, Islamabad, Multan),
critical infrastructure demands (hospitals & residential baselines),
AI data center capacities, synthetic AI workloads, and real-time grid emergencies.
"""

import copy
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Region:
    id: str
    name: str
    total_supply_mw: float       # Total grid generation (MW)
    hospital_demand_mw: float     # Non-negotiable hospital power (MW)
    residential_demand_mw: float  # Non-negotiable residential power (MW)
    reserve_margin_mw: float      # Frequency regulation reserve (MW)
    carbon_intensity_g_kwh: float # Carbon intensity (g CO2/kWh == kg CO2/MWh)
    is_active: bool = True
    disaster_note: str = "Normal operation"

    @property
    def critical_demand_mw(self) -> float:
        """Total protected demand that must never be shed or compromised."""
        return self.hospital_demand_mw + self.residential_demand_mw

    @property
    def available_ai_power_mw(self) -> float:
        """
        Calculates electricity available for flexible computing workloads:
        P_AI = max(0, Supply - Critical_Demand - Reserve)
        """
        if not self.is_active:
            return 0.0
        net = self.total_supply_mw - self.critical_demand_mw - self.reserve_margin_mw
        return max(0.0, round(net, 2))


@dataclass
class DataCenter:
    id: str
    region_id: str
    total_gpus: int
    max_power_mw: float
    current_gpus_available: int
    operational_status: str = "Active"  # Active, Degraded, Offline

    @property
    def gpu_utilization_pct(self) -> float:
        if self.total_gpus == 0:
            return 0.0
        used = self.total_gpus - self.current_gpus_available
        return round((used / self.total_gpus) * 100.0, 1)


@dataclass
class AIJob:
    id: str
    name: str
    priority: str          # "High", "Medium", "Low"
    power_mw: float        # Power requirement in MW
    gpu_requirement: int   # Number of GPUs needed
    deadline_hours: int    # Execution deadline in hours
    interruptible: bool    # Can job be paused/postponed
    origin_region: str     # Originating region
    assigned_region: Optional[str] = None
    status: str = "Pending"  # "Pending", "Running", "Postponed", "Migrated"
    estimated_emissions_kg: float = 0.0

    @property
    def priority_score(self) -> int:
        mapping = {"High": 3, "Medium": 2, "Low": 1}
        return mapping.get(self.priority, 1)


class GridSimulation:
    """Manages the full state of the electricity network, data centers, and workloads."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        self.regions: Dict[str, Region] = {}
        self.datacenters: Dict[str, DataCenter] = {}
        self.jobs: List[AIJob] = []
        self.active_disaster: Optional[str] = None
        self.initialize_default_state()

    def initialize_default_state(self):
        """Creates the 4 baseline geographical grid nodes in Pakistan."""
        self.regions = {
            "Karachi": Region(
                id="Karachi",
                name="Karachi Coastal Grid (K-Electric)",
                total_supply_mw=80.0,
                hospital_demand_mw=20.0,      # Civil Hospital, JPMC, NICVD
                residential_demand_mw=25.0,    # Dense urban residential fans/pumps
                reserve_margin_mw=10.0,
                carbon_intensity_g_kwh=420.0,  # Thermal Gas/RLNG mix
                is_active=True,
                disaster_note="Nominal grid balance"
            ),
            "Lahore": Region(
                id="Lahore",
                name="Lahore Industrial Grid (LESCO)",
                total_supply_mw=70.0,
                hospital_demand_mw=15.0,      # Mayo Hospital, Services, Jinnah
                residential_demand_mw=25.0,
                reserve_margin_mw=10.0,
                carbon_intensity_g_kwh=220.0,  # Combined Cycle & Solar mix
                is_active=True,
                disaster_note="Nominal grid balance"
            ),
            "Islamabad": Region(
                id="Islamabad",
                name="Islamabad / Northern Hydro (IESCO)",
                total_supply_mw=60.0,
                hospital_demand_mw=15.0,      # PIMS, Shifa
                residential_demand_mw=20.0,
                reserve_margin_mw=8.0,
                carbon_intensity_g_kwh=85.0,   # Clean Tarbela/Mangla Hydro
                is_active=True,
                disaster_note="Nominal grid balance"
            ),
            "Multan": Region(
                id="Multan",
                name="Multan / South Punjab Solar Grid (MEPCO)",
                total_supply_mw=50.0,
                hospital_demand_mw=18.0,      # Nishtar Hospital
                residential_demand_mw=24.0,
                reserve_margin_mw=5.0,
                carbon_intensity_g_kwh=310.0,  # Solar & Peaker mix
                is_active=True,
                disaster_note="Nominal grid balance"
            ),
        }

        self.datacenters = {
            "Karachi": DataCenter(
                id="DC-Karachi",
                region_id="Karachi",
                total_gpus=200,
                max_power_mw=25.0,
                current_gpus_available=200,
                operational_status="Active"
            ),
            "Lahore": DataCenter(
                id="DC-Lahore",
                region_id="Lahore",
                total_gpus=180,
                max_power_mw=20.0,
                current_gpus_available=180,
                operational_status="Active"
            ),
            "Islamabad": DataCenter(
                id="DC-Islamabad",
                region_id="Islamabad",
                total_gpus=160,
                max_power_mw=18.0,
                current_gpus_available=160,
                operational_status="Active"
            ),
            "Multan": DataCenter(
                id="DC-Multan",
                region_id="Multan",
                total_gpus=120,
                max_power_mw=12.0,
                current_gpus_available=120,
                operational_status="Active"
            ),
        }

        self.jobs = self.generate_synthetic_workloads(count=120)
        self.active_disaster = "Normal Baseline (No Outages)"

    def generate_synthetic_workloads(self, count: int = 120) -> List[AIJob]:
        """Generates realistic AI jobs with local critical vs flexible batch categories."""
        random.seed(self.seed)
        job_templates = [
            # High priority (Local medical vision, flood emergency telematics - MUST STAY LOCAL)
            ("Emergency Hospital Radiology AI (Civil Hospital)", "High", (1.0, 2.5), (8, 24), False),
            ("Indus Basin Flood Surge Telematics", "High", (1.5, 3.0), (16, 32), False),
            ("Real-Time Urban Heat Stroke Diagnostic Stream", "High", (1.0, 2.0), (8, 16), False),
            ("National Transmission Grid Frequency Monitor", "High", (2.0, 3.5), (16, 32), True),
            # Medium priority (Model fine-tuning, scheduled evaluations - FLEXIBLE)
            ("Urdu Foundation LLM Checkpoint Evaluation", "Medium", (2.0, 4.0), (32, 64), True),
            ("Multimodal Speech Translation Batch", "Medium", (1.5, 3.0), (16, 48), True),
            ("Agricultural Crop Blight Satellite Detection", "Medium", (2.5, 4.5), (32, 64), True),
            ("City Traffic Signal Flow Optimizer", "Medium", (1.0, 2.5), (16, 32), True),
            # Low priority (Non-urgent research experiments, synthetic data generation - CAN STEP ASIDE)
            ("Text-to-Video Diffusion Latent Crawl", "Low", (2.0, 5.0), (32, 64), True),
            ("RLHF Chatbot Preference Alignment Batch", "Low", (1.5, 3.5), (16, 48), True),
            ("Synthetic 3D Scene Asset Generation", "Low", (2.5, 5.0), (32, 64), True),
            ("Automated Hyperparameter Grid Search", "Low", (1.0, 3.0), (16, 32), True),
        ]

        jobs = []
        regions_list = ["Karachi", "Lahore", "Islamabad", "Multan"]
        for i in range(1, count + 1):
            tmpl = random.choice(job_templates)
            name_base, priority, p_range, gpu_range, interruptible = tmpl
            power = round(random.uniform(p_range[0], p_range[1]), 1)
            gpus = random.choice([8, 16, 24, 32, 48, 64])
            deadline = random.randint(2, 12)
            origin = random.choice(regions_list)

            job = AIJob(
                id=f"JOB-{i:03d}",
                name=f"{name_base} #{i}",
                priority=priority,
                power_mw=power,
                gpu_requirement=gpus,
                deadline_hours=deadline,
                interruptible=interruptible,
                origin_region=origin,
                assigned_region=None,
                status="Pending"
            )
            jobs.append(job)
        return jobs

    # ------------------ Contingency Simulation Events ------------------

    def trigger_heatwave_karachi(self):
        """
        Event 1: Peak June Afternoon in Karachi
        - Temperatures hit 48°C; every fan, pump, and AC is running.
        - Residential electricity demand surges by +15 MW.
        - Karachi power available for flexible AI drops to zero.
        - AI workloads must step aside so homes and hospitals stay on!
        """
        self.initialize_default_state()
        karachi = self.regions["Karachi"]
        karachi.residential_demand_mw = 25.0 + 15.0  # 40.0 MW
        karachi.disaster_note = "CRITICAL PEAK: 48°C Heatwave; residential fans/AC surged +15 MW"

        self.active_disaster = "Karachi Peak Heatwave (+15 MW Residential Demand)"

    def trigger_flood_dadu(self):
        """
        Event 2: Dadu / Guddu Substation Flood Inundation
        - Severe monsoon floods submerge major southern grid substations.
        - Regional generation supply drops by 60%.
        - Local data center loses 50% GPU capacity due to water ingress.
        """
        self.initialize_default_state()
        karachi = self.regions["Karachi"]
        dc_karachi = self.datacenters["Karachi"]

        karachi.total_supply_mw = round(80.0 * 0.40, 1)  # 32.0 MW (fell 60%)
        karachi.disaster_note = "EMERGENCY: Substation flood inundation; 60% generation offline"

        dc_karachi.total_gpus = int(200 * 0.50)          # 100 GPUs
        dc_karachi.current_gpus_available = dc_karachi.total_gpus
        dc_karachi.max_power_mw = 12.5
        dc_karachi.operational_status = "Degraded (50% Flooded)"

        self.active_disaster = "Flood Inundation (Guddu/Dadu 60% Offline)"

    def trigger_outage_lahore(self):
        """
        Event 3: Transmission Line Trip in Lahore
        - Grid trip severs the central transmission interconnect.
        - Lahore regional supply drops to zero; grid node becomes offline.
        - Workloads in Lahore must immediately migrate to Islamabad / Multan.
        """
        self.initialize_default_state()
        lahore = self.regions["Lahore"]
        dc_lahore = self.datacenters["Lahore"]

        lahore.total_supply_mw = 0.0
        lahore.is_active = False
        lahore.disaster_note = "BLACKOUT: Transmission line tripped; node isolated"

        dc_lahore.total_gpus = 0
        dc_lahore.current_gpus_available = 0
        dc_lahore.max_power_mw = 0.0
        dc_lahore.operational_status = "Offline"

        self.active_disaster = "Transmission Trip (Lahore 100% Blackout)"

    def reset_to_normal(self):
        """Restores the grid to normal operating conditions."""
        self.initialize_default_state()
        self.active_disaster = "Normal Baseline (No Outages)"

    # Backward-compatible method aliases
    trigger_heatwave_south = trigger_heatwave_karachi
    trigger_flood_north = trigger_flood_dadu
    trigger_outage_east = trigger_outage_lahore
