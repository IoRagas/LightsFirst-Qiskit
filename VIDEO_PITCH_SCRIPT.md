# Lights First: 3-Minute Video Pitch & Demo Script
**Title:** Lights First: AI work that steps aside when the city needs power  
**Competition:** Qiskit Hackathon 2026 | **Target Track:** Energy & Smart Infrastructure  
**Video Length:** Exactly 3 Minutes (180 Seconds) | **Access:** Anyone with the link

---

## Pitch Strategy & Slide Outline

```
┌──────────────┬───────────────────────────────┬────────────────────────────────────────────────────────┐
│ Timestamp    │ Screen Visual / Slide         │ Key Spoken Narrative (Word-for-Word Script)             │
├──────────────┼───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 0:00 – 0:35  │ Visual 1: Karachi Heatwave    │ Grounded Authentic Pakistan Hook (Fans, Water Pumps)   │
│ 0:35 – 1:05  │ Visual 2: The Core Concept    │ Lights First: AI stepping aside for homes & hospitals  │
│ 1:05 – 2:05  │ Screen Recording: Live App    │ Interactive Dashboard: Heatwave, Flood, Homes Counter  │
│ 2:05 – 2:35  │ Visual 3: Qiskit QAOA Core    │ 8-Qubit Deficit QUBO, Exact Ground Truth & NISQ Limits │
│ 2:35 – 3:00  │ Visual 4: Summary & Delivery  │ GitHub Repo, Word Report, 100% Life-Support Shielded   │
└──────────────┴───────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## Word-for-Word Script (180 Seconds)

### [0:00 – 0:35] PART 1: The Authentic Hook — Hot June Afternoon in Karachi
*(Visual: Photos/footage of Karachi street life in summer, fans turning, followed by data center server racks.)*

> **Speaker:**  
> "Picture this: A hot June afternoon in Karachi. Temperatures cross 45 degrees Celsius. Every ceiling fan, water pump, and air conditioner is running, and the power company simply does not have enough electricity for everyone.  
> Across town, a massive building full of computers—a data center—is training an AI model, consuming megawatts of electricity around the clock.  
> To cope, the utility company cuts residential feeders. Neighborhoods go dark, fans stop, and water pumps shut down. Meanwhile, that AI training keeps running—even though it didn't need to run here or now. It could easily run in Lahore, where power was spare, or tonight, when the heat subsides."

---

### [0:35 – 1:05] PART 2: The Core Concept — Lights First
*(Visual: Architecture diagram showing Karachi, Lahore, Islamabad, Multan interconnects and the priority firewall.)*

> **Speaker:**  
> "We built **Lights First**—an autonomous orchestrator that ensures flexible AI compute steps aside the moment a city needs power.  
> When local electricity gets tight, power stays with homes, water pumps, and intensive care units at Civil Hospital and JPMC. Flexible AI jobs migrate across clean provincial corridors—like northern hydro in Islamabad—or slide to night. Meanwhile, urgent local tasks—like a hospital's AI analyzing emergency CT scans—stay running right here without interruption.  
> But we cannot move everything blindly: data transfer takes time, jobs have hard deadlines, and destination grids cannot absorb every workload at once. Every choice couples to every other. Even 50 jobs across 4 cities and time windows create a combinatorial search space with over 70 digits of possibilities."

---

### [1:05 – 2:05] PART 3: Live Interactive Demo
*(Visual: Live screen recording of the Streamlit application `http://localhost:8501`.)*

> **Speaker:**  
> *(Action: Show normal overview tab)*  
> "Here is our live industrial console. We monitor four provincial grids: Karachi, Lahore, Islamabad, and Multan. Over 68 Megawatts of hospital life-support are mathematically locked as non-negotiable baselines.  
> *(Action: Click 'Trigger Karachi Heatwave' in the sidebar)*  
> Watch what happens when a 48-degree heatwave hits Karachi. Residential demand surges by 15 Megawatts. The Karachi power bar turns amber.  
> Look at our 'Homes Kept Powered' counter: over 16,000 homes kept their fans and water pumps running because non-urgent AI workloads stepped aside in sub-seconds!  
> *(Action: Show Workload Scheduling tab)*  
> Flexible LLM training jobs instantly migrate to clean hydro in Islamabad or postpone, while emergency radiology AI at Civil Hospital remains 100% active and shielded on local microgrid power.  
> *(Action: Click 'Indus Basin Flood')*  
> When monsoon floods submerge generation substations, the system instantly recalculates available power, isolates vulnerable lines, and re-routes workloads without a single hospital outage."

---

### [2:05 – 2:35] PART 4: Qiskit 2.x QAOA Core & Classical Ground Truth
*(Visual: Switch to Tab 4 'Qiskit QAOA Core' showing the convergence trajectory and benchmark table.)*

> **Speaker:**  
> "When extreme contingency forces competing critical workloads into a tight clean corridor, Lights First maps the decision to an 8-qubit constrained deficit QUBO using Qiskit Optimization.  
> We evaluate our parameterized QAOA circuit using statevector simulation and classical COBYLA feedback against an exact classical brute-force ground truth evaluating all 256 states.  
> Our Qiskit QAOA solver reaches an approximation ratio of **99.7%**, reliably identifying the exact Pareto optimal state.  
> And we are completely honest about NISQ limitations: on physical transmons, 64 CNOT gates suffer from gate noise and heavy-hex SWAP overhead. That is why our dual-tier design uses classical heuristics for macro dispatch and QAOA for the high-stakes combinatorial bottleneck."

---

### [2:35 – 3:00] PART 5: Impact & Conclusion
*(Visual: Summary slide with GitHub repository link, Word technical report preview, and final deliverables.)*

> **Speaker:**  
> "Lights First shows that quantum computing can solve problems grounded in basic human dignity.  
> Our complete submission package includes our open-source Qiskit repository, the live interactive Streamlit console, a comprehensive Word technical report with full classical baselines, and this presentation.  
> When power is scarce, lights and lives must come first. Thank you!"

---

## Demo Recording Checklist for Team
- [ ] Open Streamlit app at `http://localhost:8501`.
- [ ] Ensure full screen resolution (1080p).
- [ ] Keep speech pacing natural, empathetic, and clear (approx. 130–140 words per minute).
- [ ] Click 'Trigger Karachi Heatwave' at ~1:15 to show the +16,000 Homes Kept Powered counter.
- [ ] Switch to Tab 4 'Qiskit QAOA Core' at ~2:05.
- [ ] Click 'Qiskit Quantum Core' tab at ~2:00.
- [ ] Upload final MP4 to Google Drive and verify permissions: "Anyone with the link can view".
