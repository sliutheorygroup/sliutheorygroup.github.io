# Oxygen Displacement

林子越  

本教程用于计算 HfO₂ 体系中 **每个氧原子** 相对于其近邻规整四面体几何中心的位移，并据此判断结构是否具有全局极化。

---

## 代码

```python
from ase import Atoms
from ase.io import read
import numpy as np


def signed_volume(a, b, c, d):
    """计算由点 a, b, c, d 定义的四面体的有向体积"""
    return np.dot(np.cross(b - a, c - a), d - a) / 6.0


def is_point_in_tetrahedron(P, A, B, C, D, tol=0.02):
    """判断点 P 是否在由点 A, B, C, D 定义的四面体内"""
    # 计算各小四面体的有向体积
    V0 = signed_volume(A, B, C, D)
    V1 = signed_volume(P, B, C, D)
    V2 = signed_volume(A, P, C, D)
    V3 = signed_volume(A, B, P, D)
    V4 = signed_volume(A, B, C, P)

    # 符号一致 → 点在内部（允许 ±tol 误差）
    signs = np.array([V0, V1, V2, V3, V4])
    positive = signs > -tol
    negative = signs <  tol
    return np.all(positive) or np.all(negative)


# ---------- 主程序 ----------

# 读取 POSCAR
atoms = read("POSCAR")

# 分别取得 Hf / O 的索引
Hf_indices = [i for i, at in enumerate(atoms) if at.symbol == "Hf"]
O_indices  = [i for i, at in enumerate(atoms) if at.symbol == "O"]

# 为每个原子生成“第几个同元素原子”的编号
element_specific_indices = {}
counter = {}
for i, at in enumerate(atoms):
    counter[at.symbol] = counter.get(at.symbol, 0) + 1
    element_specific_indices[i] = counter[at.symbol]

sum_dx = sum_dy = sum_dz = 0.0
valid_O_count = 0
O_displacements = {}

with open("B4ID.dat", "w") as f_b4id, open("O-disp.dat", "w") as f_disp:

    for i in O_indices:
        O_pos = atoms.get_positions()[i]

        # O-Hf 距离（考虑周期性）
        distances = [(j, atoms.get_distance(i, j, mic=True)) for j in Hf_indices]
        distances.sort(key=lambda x: x[1])

        first_three = [idx for idx, _ in distances[:3]]
        found = False

        # 依次尝试第 4 个 Hf
        for fourth in (idx for idx, _ in distances[3:]):
            cand = first_three + [fourth]

            # 取得 4 个 Hf 的最小影像坐标
            Hf_pos = [
                O_pos + atoms.get_distance(i, idx, mic=True, vector=True)
                for idx in cand
            ]

            # 四条边必须都 < 5 Å
            edges = [
                atoms.get_distance(cand[m], cand[n], mic=True)
                for m in range(4) for n in range(m + 1, 4)
            ]
            if np.all(np.array(edges) < 5.0):
                # 写入 B4ID.dat
                f_b4id.write(" ".join(map(str, cand)) + "\n")
                found = True

                # 四面体质心
                center = np.mean(np.array(Hf_pos), axis=0)

                # 位移 Δ⃗
                dx, dy, dz = O_pos - center
                f_disp.write(f"{dx:.6f} {dy:.6f} {dz:.6f}\n")

                O_displacements[i] = (dx, dy, dz)
                sum_dx += dx; sum_dy += dy; sum_dz += dz
                valid_O_count += 1
                break

        if not found:
            # 未配位
            num = element_specific_indices[i]
            f_b4id.write(f"O 原子 {num} 未找到合适的第 4 个 Hf 原子\n")
            O_displacements[i] = (0.0, 0.0, 0.0)


# 平均位移
if valid_O_count:
    avg_dx = sum_dx / valid_O_count
    avg_dy = sum_dy / valid_O_count
    avg_dz = sum_dz / valid_O_count
    with open("avgdisp.dat", "w") as f:
        f.write(f"{avg_dx:.6f} {avg_dy:.6f} {avg_dz:.6f}\n")
    print(f"平均位移: ({avg_dx:.6f}, {avg_dy:.6f}, {avg_dz:.6f}) Å")
else:
    print("没有找到任何有效的 O 原子四面体。")


# 生成 POSCAR.xsf（带位移向量）
with open("POSCAR.xsf", "w") as f:
    f.write("CRYSTAL\nPRIMVEC\n")
    for v in atoms.get_cell():
        f.write(f" {v[0]:.16f} {v[1]:.16f} {v[2]:.16f}\n")

    f.write("PRIMCOORD\n")
    f.write(f"{len(atoms)}\n")

    for i, at in enumerate(atoms):
        x, y, z = atoms.get_positions()[i]
        if at.symbol == "Hf":
            f.write(f"Hf {x:.8f} {y:.8f} {z:.8f} 0.00000000 0.00000000 0.00000000\n")
        else:
            dx, dy, dz = O_displacements[i]
            f.write(f"O  {x:.8f} {y:.8f} {z:.8f} {dx:.6f} {dy:.6f} {dz:.6f}\n")
```

---

## 四面体-位移算法说明

### 1. 判断“点是否在四面体内部”——有向体积判据
给定四个顶点 **A B C D** 构成的四面体，其有向体积  

```
V₀ = [(B−A) × (C−A)] · (D−A) / 6
```

对任意待测点 **P** 再构造 4 个“小”四面体  

```
V₁ = V(P,B,C,D)   V₂ = V(A,P,C,D)
V₃ = V(A,B,P,D)   V₄ = V(A,B,C,P)
```

* 若 `V₁ … V₄` 与 `V₀` **符号一致**，P 在内部；  
* 若某些 Vᵢ≈0，则 P 位于面 / 棱上；  
* 若符号不全同，P 在外部。  

代码中使用 ±`tol` 容差，只要 5 个体积全部 > −tol 或 < tol 即视作“同号”。

### 2. 为 O 找到 4 个配位 Hf

1. 对每个 O 原子，计算到所有 Hf 的最小影像距离；  
2. 距离升序排序，最近 **3 个** 一定采用；  
3. 依次尝试第 4 近的 Hf，只有当 **4 个 Hf 的 6 条边全部 < 5 Å** 时接受；  
4. 质心  

   ```
   r₀ = (r₁ + r₂ + r₃ + r₄) / 4
   ```

   位移（极化矢量）  

   ```
   Δ⃗ = r(O) − r₀
   ```

   写入 `O-disp.dat`。找不到合格第四顶点时记为“未配位”。

### 3. 交互式 3D 可视化

保存下列 **完整 HTML** 为 `view_tetra.html`，即可用浏览器查看：

* 左侧下拉框可选择任意 O 原子  
* 场景元素  
  * 灰球：全部 Hf  
  * 粉球：全部 O  
  * **红球**：选中 O  
  * **金球**：构成四面体的 4 Hf  
  * 黄线：四面体 6 条棱  
  * 绿球：质心  
  * 蓝箭头：极化矢量 Δ⃗  
* 支持拖拽旋转与缩放

[🔗 点击查看交互式演示](./tetrahedron_demo.html)

---

以上内容同时给出了算法解释与可视化示例，便于进一步调试或展示。