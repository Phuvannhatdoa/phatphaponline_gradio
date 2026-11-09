import subprocess, os, sys
DAO = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
os.chdir(DAO)
SESS = os.path.join(DAO, r"docs\sessions\2026-10-26\task-id-merge")
mode = sys.argv[1]
if mode == "dup":
    cmd = ["python", "-X", "utf8", "scripts/build_progress_data.py", "--check-dup-ids"]
    out_path = os.path.join(SESS, "dupids.txt")
elif mode == "pipeline":
    cmd = ["cmd", "/c", "npm", "run", "pipeline"]
    out_path = os.path.join(SESS, "pipeline.log")
else:
    sys.exit("bad mode")
r = subprocess.run(cmd, capture_output=True, cwd=DAO, shell=False)
text = "=== CMD: " + " ".join(cmd) + "\n=== RC: " + str(r.returncode) + "\n=== STDOUT ===\n" + r.stdout.decode("utf-8", "replace") + "\n=== STDERR ===\n" + r.stderr.decode("utf-8", "replace")
open(out_path, "w", encoding="utf-8").write(text)
print(text[-3000:])
print("RC", r.returncode, "saved", out_path, "bytes", len(text))
