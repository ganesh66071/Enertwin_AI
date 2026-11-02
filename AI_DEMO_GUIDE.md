# EnerTwin AI Demo Guide

## Demo sequence

1. Start the backend and frontend.
2. Select Vignan University (CAMP001).
3. Confirm the campus dashboard shows the expected energy profile.
4. Open the AI Anomalies screen.
5. Review the top anomaly and root-cause explanation.
6. Open the Forecast section and check the next peak forecast.
7. Move to the Simulation page and try HVAC reduction at 15%.
8. Run the simulation and review the projected energy, cost, and CO2 impact.
9. Open the AI Analyst and ask: "Why should we optimize HVAC?"
10. Ask: "How much can we save?"
11. Switch to VIIT and validate the outputs change.
12. Switch to Vignan Pharma and validate the outputs change again.

## Expected behavior

- All AI results stay campus-specific.
- Switching campuses refreshes anomalies, forecast, optimization, and analyst output.
- LLM failure falls back to deterministic ML-generated insights.
- The dashboard continues to function even if AI services are unavailable.
