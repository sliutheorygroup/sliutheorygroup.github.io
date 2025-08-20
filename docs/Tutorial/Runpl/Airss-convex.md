# run.pl（AIRSS 产生凸包图脚本）

作者：林子越  

---

## 1. 拷贝所需的结构文件

1. 列出结构并拷贝所选的 `.res`（或 `.param`）文件到当前文件夹：
   ```bash
   ca -m -de <阈值>
   ```
2. 将 AIRSS 搜索得到的 `.res` 文件复制到 **test** 目录：
   ```bash
   cp *.res test/
   ```
3. 同时把对应的初始 `.cell`、`.param` 文件也拷入 **test**。

### 1.1 仅保留最稳定配比

```bash
ca -f *** -r -t | awk '{print $1".res"}' | xargs cp -t tmp/
```

---

## 2. 可选的快速筛选方法（可跳过）

```bash
# 列出离凸包 0.05 eV 以内的点并删除其余 .res
ca -m -de 0.05 --delete
```

1. 将 `.res` 文件复制到 **test**：
   ```bash
   cp *.res test/
   ```
2. 删除单个原子能量差大于 0.04 eV 的结构（0.04 可按需调整）：
   ```bash
   ca -m -de 0.04 -r --delete
   ```
3. 提高 **cell** 中的 K 点密度并加上压力；在 **param** 中提高截断能，并加入  
   ```text
   WRITE_CIF_STRUCTURE : true
   ```
   这样可直接得到 CIF 文件，无需再用 VESTA 转换。
4. 通过 `run.pl` 连续计算 **test** 中所有结构：
   ```bash
   run.pl -mpinp 8 -keep
   ```
5. 比较各结构的焓值，焓值最低者即为最稳定结构。

### 2.1 建立 tmp 文件夹并拷贝候选结构

```bash
mkdir -p tmp
ca -m -de 0.05 | awk '{print $1".res"}' | xargs cp -t tmp/
```

选择某一配比前 10 个稳定结构：
```bash
ca -m | sort -n -k 6 -k 5 | head -n 10 | awk '{print $1".res"}' | xargs cp -t tmp/
```

---

## 3. 提高计算精度

1. 在初始 `.cell` 文件中增密 K 点（例如由 0.07 改为 0.03），并在末尾设置压力。
2. 在 `.param` 文件中提高截断能。

---

## 4. 提交 PBS 任务

`runpl.pbs` 示例：
```bash
#!/bin/bash
#PBS -q CT1
#PBS -l nodes=1:ppn=12
#PBS -j oe
#PBS -V
#PBS -N run.pl

cd "$PBS_O_WORKDIR"
run.pl -mpinp 12
```

提交任务：
```bash
qsub runpl.pbs
```

---

## 5. 查看结果

计算结束后：
* 各结构对应的 `.res` 文件中包含最终 K 点网格与截断能。
* `jobs.txt` 记录已优化完成的结构。

---

## Notes

1. 部分服务器生成的 `.res` 可能含有空行，导致 `ca -m` / `ca -s` 显示异常，可用：
   ```bash
   sed -i '/^$/d' *.res
   ```
2. 以元素 **A** 和 **B** 为参考线绘制凸包图：
   ```bash
   ca -m -1 A -2 B | sort -n -k 6 -k 5
   ```