"""Run on your local checkout, not inside Actions. Creates GitHub-required path."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parent
target=root/'.github/workflows/monthly.yml'
if target.exists(): raise SystemExit('Already exists: inspect before replacing.')
target.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(root/'workflows/monthly.yml',target)
print('Created .github/workflows/monthly.yml. Commit and push to GitHub.')
