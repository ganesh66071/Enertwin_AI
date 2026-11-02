import os
import glob
import re

print("="*60)
print("TASK 8: ENGINEERING FACTS AUDIT")
print("="*60)

# Lines of code per language
extensions = {
    "Python": [".py"],
    "TypeScript/TSX": [".ts", ".tsx"],
    "JavaScript/JSX": [".js", ".jsx", ".mjs"],
    "CSS": [".css"],
    "JSON": [".json"],
    "Markdown": [".md"],
    "HTML": [".html"]
}

loc_by_lang_backend = {}
loc_by_lang_frontend = {}

for root, dirs, files in os.walk("."):
    # Skip node_modules, .git, venv, .gemini, audit_scripts
    if any(x in root for x in ["node_modules", ".git", "venv", ".gemini", "audit_scripts", ".next"]):
        continue
    is_backend = root.startswith(".\\backend") or root.startswith("./backend")
    is_frontend = root.startswith(".\\frontend") or root.startswith("./frontend")
    
    for f in files:
        ext = os.path.splitext(f)[1]
        lang = None
        for l, exts in extensions.items():
            if ext in exts:
                lang = l
                break
        if not lang:
            continue
            
        fpath = os.path.join(root, f)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                lines = len(fp.readlines())
        except Exception:
            continue
            
        if is_backend:
            loc_by_lang_backend[lang] = loc_by_lang_backend.get(lang, 0) + lines
        elif is_frontend:
            loc_by_lang_frontend[lang] = loc_by_lang_frontend.get(lang, 0) + lines

print("BACKEND Lines of Code by Language:")
for lang, count in sorted(loc_by_lang_backend.items()):
    print(f"  {lang}: {count}")
print(f"  Total Backend LOC: {sum(loc_by_lang_backend.values())}")

print("\nFRONTEND Lines of Code by Language:")
for lang, count in sorted(loc_by_lang_frontend.items()):
    print(f"  {lang}: {count}")
print(f"  Total Frontend LOC: {sum(loc_by_lang_frontend.values())}")

# Number of frontend pages and components
frontend_pages = []
frontend_components = []
for root, dirs, files in os.walk("frontend"):
    if any(x in root for x in ["node_modules", ".git", ".next"]):
        continue
    for f in files:
        fpath = os.path.join(root, f)
        if "frontend\\app" in root or "frontend/app" in root:
            if f in ["page.tsx", "page.jsx", "page.js"]:
                frontend_pages.append(fpath)
        if "frontend\\components" in root or "frontend/components" in root:
            if f.endswith((".tsx", ".jsx")):
                frontend_components.append(fpath)

print(f"\nFrontend Pages count: {len(frontend_pages)}")
for p in sorted(frontend_pages):
    print(f"  Page: {p}")

print(f"\nFrontend Components count: {len(frontend_components)}")
for c in sorted(frontend_components):
    print(f"  Component: {c}")

# Number of backend modules
backend_modules = []
for root, dirs, files in os.walk("backend"):
    if any(x in root for x in ["__pycache__", ".git"]):
        continue
    for f in files:
        if f.endswith(".py"):
            backend_modules.append(os.path.join(root, f))
print(f"\nBackend Python Modules count: {len(backend_modules)}")

# Docker compose
docker_files = glob.glob("*docker*") + glob.glob("*/*docker*")
print(f"\nDocker files found: {docker_files}")
if docker_files:
    for df in docker_files:
        print(f"  {df}")
else:
    print("  No docker-compose.yml or Dockerfile found.")

# Test users / sessions in DB or mock
print("\nChecking test users / sessions in app.db or codebase...")
# Check auth in frontend

