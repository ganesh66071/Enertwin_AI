with open(r"C:\Users\Ganesh B\.gemini\antigravity\brain\e87a2cf4-aafd-475d-a9f8-62373acc5031\.system_generated\tasks\task-196.log", "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if "Endpoint:" in line or "Status:" in line or "Average" in line or "Median" in line or "p95" in line or "Pipeline" in line:
            print(line.strip())

