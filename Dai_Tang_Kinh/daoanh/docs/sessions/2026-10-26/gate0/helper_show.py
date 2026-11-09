import subprocess, sys
# usage: python helper_show.py <git-spec> <out-file>
# Ghi nguyen bytes cua `git show <spec>` ra file (khong qua pipe PowerShell).
spec, out = sys.argv[1], sys.argv[2]
data = subprocess.run(["git", "show", spec], capture_output=True, check=True).stdout
with open(out, "wb") as f:
    f.write(data)
print("bytes", len(data), "lines", data.count(b"\n"))
