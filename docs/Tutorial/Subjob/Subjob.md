
# 自动提交/重提任务  
林子越  

单独把这两个脚本拎出来讲，是因为它们在实际工作中非常好用：  
* 自动提交脚本能够控制自己的排队任务数量；  
* 重提脚本可以监控已提交任务的运行时长，并在需要时自动取消 / 重提。  

下面仅给出核心思路与示范代码，真正要执行的具体命令请在 `TODO` 位置自行补充。

---

## 自动提交

仅保留两件事：  

1. 监控调度队列，直到空出足够配额再继续；  
2. 判断本地标记文件是否满足条件，决定是否往下做。  

```bash
#!/usr/bin/env bash
#
# queue-watch + continue-or-not
#
# ────────────────────────────────────────────────
# 目录定位（可按需修改）
workdir="$(pwd)"
cd "$workdir" || exit 1
# ────────────────────────────────────────────────
# ① 监测队列：若当前用户的作业数 ≥ 21 就等待
#    注：按需把 21、sleep 时间等阈值换成自己的
while true; do
    # 只统计自己在队列中的作业数，去掉表头行
    njob=$(squeue -u "$USER" | tail -n +2 | wc -l)
    if (( njob < 21 )); then              # 队列够空，放行
        break
    fi
    printf "队列里还有 %d 个任务，休眠 20 s...\n" "$njob"
    sleep 20
done
# ────────────────────────────────────────────────
# ② 判断是否继续：文件不存在或内容不含关键字则继续
flagfile="zToten.dia"
if [[ ! -f $flagfile ]] || ! grep -q "TOTEN" "$flagfile"; then
    echo "⚠️ 需要继续后续操作（文件缺失或不完整）"
    # =====================================================
    # TODO: 在这里写真正要执行的命令，例如：
    # sbatch Runscript
    # python postprocess.py
    # ...
    # =====================================================
else
    echo "✅ 检测到正常完成标记，跳过后续操作"
fi
```

### 要点提醒
* `squeue -u "$USER"` 仅查看自己的作业；若无 Slurm 可换成相应命令。  
* `tail -n +2` 去掉表头行，保证 `wc -l` 得到纯数字。  
* `grep -q` 静默模式，只判断是否命中关键字。  
* 阈值（21）、睡眠间隔、关键字及标记文件名可按项目需求自行调整。  

---

## 重提任务

该脚本仅保留：  

1. 监测 SLURM 队列中任务运行时长；  
2. 根据任务名与工作目录关键字筛选需处理的任务；  
3. （可选）通过 `ps aux` 二次确认任务确属当前账号；  
4. 提供“仅删除（scancel）超时任务 / 继续自定义操作”两种选择。  

真正的“后续操作”留在 `TODO` 占位符处，由你按需补充。

```python
#!/usr/bin/env python3
"""
watch_slurm_timeout.py

• 监视当前用户的 SLURM 作业运行时长
• 支持按任务名、工作目录关键字过滤
• 提供:
  --only-cancel  只取消超时任务
  交互式 [C]ancel / [O]ther / [S]kip 选择
"""
import argparse
import os
import re
import subprocess
import sys
from typing import List, Tuple

# ---------- 通用工具 ---------- #
def run(cmd: str) -> str:
    """执行 shell 命令并返回字符串结果（出错直接退出）。"""
    try:
        return subprocess.check_output(
            cmd, shell=True, text=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        sys.exit(f"[ERROR] 命令失败: {cmd}\n{e.output}")

def hms_to_seconds(t: str) -> int:
    """
    将 squeue 的 TIME 列转换为秒.
    可能格式:
        D-HH:MM:SS
        HH:MM:SS
        MM:SS
        SS
    """
    if "-" in t:                           # D-HH:MM:SS
        days, hms = t.split("-")
        h, m, s = map(int, hms.split(":"))
        return int(days) * 86400 + h * 3600 + m * 60 + s
    parts = list(map(int, t.split(":")))
    if len(parts) == 3:                    # HH:MM:SS
        h, m, s = parts
    elif len(parts) == 2:                  # MM:SS
        h, m, s = 0, *parts
    else:                                  # SS
        h, m, s = 0, 0, parts[0]
    return h * 3600 + m * 60 + s

# ---------- SLURM 相关 ---------- #
def get_job_workdir(jobid: str) -> str:
    """通过 scontrol 抓取作业工作目录 (WorkDir 或 StdOut 路径的上级目录)。"""
    info = run(f"scontrol show job {jobid}")
    # WorkDir 字段
    m = re.search(r"WorkDir=(\S+)", info)
    if m:
        return m.group(1)
    # 退而求其次：StdOut=.../slurm-xxx.out → 抽取目录
    m = re.search(r"StdOut=(.*)/slurm-\d+\.out", info)
    if m:
        return m.group(1)
    return "UNKNOWN"

def list_timeout_jobs(
    threshold_sec: int,
    job_name: str,
    path_keyword: str
) -> List[Tuple[str, str, str]]:
    """返回满足条件的 (jobid, workdir, raw_time_string) 列表。"""
    user = os.getenv("USER")
    sq = run(f"squeue -u {user}")
    lines = sq.strip().splitlines()[1:]        # 跳过表头
    result = []
    for ln in lines:
        cols = ln.split()
        if len(cols) < 6:
            continue
        jobid, name, time_used = cols[0], cols[2], cols[5]
        if job_name and name != job_name:
            continue
        if hms_to_seconds(time_used) < threshold_sec:
            continue
        workdir = get_job_workdir(jobid)
        if path_keyword and path_keyword not in workdir:
            continue
        # ------------- 可选：ps aux 二次确认 ------------- #
        ps_ok = any(jobid in p for p in run("ps aux").splitlines())
        if not ps_ok:
            continue
        # ------------------------------------------------ #
        result.append((jobid, workdir, time_used))
    return result

def cancel_job(jobid: str):
    subprocess.run(f"scancel {jobid}", shell=True, check=False)

# ---------- 主程序 ---------- #
def main():
    parser = argparse.ArgumentParser(
        description="监视并处理运行超时的 SLURM 作业"
    )
    parser.add_argument(
        "-t", "--threshold", type=float, default=5,
        help="超时时间 (小时)，默认 5h"
    )
    parser.add_argument(
        "-n", "--name", default="Runscrip",
        help="仅匹配指定作业名"
    )
    parser.add_argument(
        "-k", "--keyword",
        default="sc90805/autobackup_BSCC-A2-sc90805/lzy",
        help="工作目录需包含的关键字子串"
    )
    parser.add_argument(
        "--only-cancel", action="store_true",
        help="检测到超时后直接 scancel，无后续操作"
    )
    args = parser.parse_args()
    timeout_sec = int(args.threshold * 3600)
    jobs = list_timeout_jobs(timeout_sec, args.name, args.keyword)
    if not jobs:
        print(">> 没有发现符合条件的超时任务。")
        return

    print("\n============= 发现超时任务 =============")
    for jid, wdir, tstr in jobs:
        print(f"{jid:>8} TIME={tstr:<10} DIR={wdir}")
    print("========================================\n")

    # --- 只取消 ---
    if args.only_cancel:
        for jid, *_ in jobs:
            cancel_job(jid)
        print(">> 已取消全部超时任务。")
        return

    # --- 交互式 ---
    choice = input(
        "[C]ancel only / [O]ther operations / [S]kip ? "
    ).strip().lower()

    if choice.startswith("c"):
        for jid, *_ in jobs:
            cancel_job(jid)
        print(">> 已取消所选任务。")

    elif choice.startswith("o"):
        for jid, wdir, _ in jobs:
            print(f"\n>>> 处理 Job {jid} ({wdir})")
            cancel_job(jid)
            # ========================================================
            # TODO: 在此处编写你自己的文件操作、重新提交等自定义逻辑
            # 例如:
            # subprocess.run("sbatch Runscript", cwd=wdir, shell=True)
            # ========================================================
    else:
        print(">> 未执行任何操作。")

if __name__ == "__main__":
    main()
```

### 使用示例

1. 直接干掉运行 ≥ 6 h 且作业名为 Runscrip 的任务  
   ```bash
   python watch_slurm_timeout.py -t 6 --only-cancel
   ```

2. 先检测，再手动选择后续动作  
   ```bash
   python watch_slurm_timeout.py -t 4
   ```

脚本结构已将“找任务 &（可选）取消”与“后续自定义操作”完全解耦，  
想做什么，只需在 `# TODO` 区域补上自己的代码即可。
```