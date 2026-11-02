import os
import sqlite3
from app.core.database import SessionLocal
from app.services.analytics_service import calculate_campus_analytics
from app.services.simulation_service import run_simulation
from ai.optimization.optimizer import generate_scenarios, choose_best_scenario, calculate_scenario
from app.core.config import get_settings

print("="*60)
print("TASK 5: OPTIMIZATION & SIMULATION OUTPUT")
print("="*60)

settings = get_settings()
tariff = settings.default_electricity_tariff
co2_factor = settings.co2_emission_factor_kg_per_kwh

print(f"Tariff (cost per kWh): {tariff} INR/kWh")
print(f"CO2 emission factor:   {co2_factor} kg CO2/kWh")

campuses = ["viit", "vignan-university", "mvv-mk-park"]

db = SessionLocal()

print("\n--- PART 1: AI OPTIMIZATION SCENARIOS (ai/optimization/optimizer.py) ---")
print("Scenarios compared per campus: 3 (Scenario A: HVAC -10%, Lighting -8%, Equipment -4%; Scenario B: HVAC -15%, Lighting -10%, Equipment -5%; Scenario C: HVAC -20%, Lighting -12%, Equipment -7%)")

for cid in campuses:
    kpis = calculate_campus_analytics(db, cid)
    baseline_energy = float(kpis.get("total_energy_kwh", 0.0))
    baseline_peak = float(kpis.get("peak_demand_kw", 0.0))
    
    scenarios = generate_scenarios(baseline_energy, baseline_peak, tariff, co2_factor)
    best = choose_best_scenario(scenarios)
    
    print(f"\nCampus: {cid.upper()}")
    print(f"  Baseline Energy: {baseline_energy:,.2f} kWh")
    print(f"  Baseline Peak:   {baseline_peak:,.2f} kW")
    print(f"  Total Scenarios Compared: {len(scenarios)}")
    for sc in scenarios:
        pct_saving = (sc['energy_saved'] / baseline_energy) * 100 if baseline_energy else 0
        print(f"    {sc['scenario']}: Projected={sc['new_energy']:,.2f} kWh | Saved={sc['energy_saved']:,.2f} kWh ({pct_saving:.2f}%) | Cost Saved={sc['cost_saved']:,.2f} | CO2 Reduced={sc['co2_saved']:,.2f} kg | ROI={sc['roi']}%")
    print(f"  Recommended Strategy: {best['recommended_action']} (Expected Energy Saved={best['expected_savings']:,.2f} kWh, Cost Saved={best['expected_cost_savings']:,.2f}, CO2 Saved={best['expected_co2_reduction']:,.2f} kg, ROI={best['roi']}%)")

print("\n--- PART 2: WHAT-IF SIMULATION (HVAC -15% SCENARIO) (app/services/simulation_service.py) ---")
print("Running simulation with: hvac_reduction_percent=15, others=0")

for cid in campuses:
    sim_res = run_simulation(db, campus_id=cid, hvac_reduction_percent=15.0)
    base = sim_res["baseline"]
    proj = sim_res["projected"]
    save = sim_res["savings"]
    pct_save = (save["energy"] / base["energy"]) * 100 if base["energy"] else 0
    print(f"\nCampus: {cid.upper()} (HVAC -15% simulation):")
    print(f"  Baseline Energy:  {base['energy']:,.2f} kWh")
    print(f"  Projected Energy: {proj['energy']:,.2f} kWh")
    print(f"  Energy Savings:   {save['energy']:,.2f} kWh ({pct_save:.2f}%)")
    print(f"  Cost Savings:     {save['cost']:,.2f} INR")
    print(f"  CO2 Reduction:    {save['co2']:,.2f} kg")
    print(f"  Peak Reduction:   {save['peak_demand']:,.2f} kW")

db.close()
print("="*60)

