# Doping/vacancy Generator

*作者：林子越*

下面这份脚本把  

1. “要替换哪些元素”  
2. “每个元素可以被哪些新元素替换”  
3. “是否要删除某个元素”  

全部集中到最前面的 **1 个字典**里。  
读者只要改动这个字典，其余部分无需再碰。

## 脚本逻辑

- 扫描 `Struct/` 中的全部 `.vasp` 文件。  
- 对每个文件逐一做掺杂／删除操作。  
- 通过 ASE 的 `SymmetryEquivalenceCheck` 去重。  
- 将每一种唯一结构写入  
  `Results/<原文件名去后缀>/<方案代号>/unique_<编号>.vasp`。  

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Doping / vacancy generator
-------------------------------------------------
把下面的 `doping_plan` 改成你自己的即可。
其余部分不要动，直接运行：
    python dopant_generator.py
需要 ASE >= 3.22
"""

import os
import itertools
from collections import OrderedDict

from ase.io import read, write
from ase.utils.structure_comparator import SymmetryEquivalenceCheck

# ================================================================
# 1. 用户区：定义掺杂 / 空位方案
# ------------------------------------------------
# 键 : 要被替换或删除的母体元素
# 值 : 一个列表
#   • 普通替换 -> 直接写元素符号，如 'La'
#   • 制造空位 -> 字符串 'VAC' (VAC = vacancy)
#
# 例子（可随意删改、增减）:
#   Hf 被 ('La', 'Y') 二选一替换
#   O  被 'VAC' 删除一个 O 产生空位
#   Al 被 'Ga' 单一掺杂
#
# 你可以只写 1 个条目，也可以写 2、3 … 最多 N 个。
# ================================================================

doping_plan = OrderedDict([
    ('Hf', ['La', 'Y']),
    ('O',  ['VAC']),      # 用 VAC 表示要删掉 O
    # ('Al', ['Ga']),     # 需要时取消注释
])

# ================================================================
# 2. 脚本区：请勿修改
# ================================================================

comp      = SymmetryEquivalenceCheck()       # 判断结构是否等价
src_dir   = 'Struct'                         # 原始 VASP 文件夹
dst_root  = 'Results'                        # 输出根目录
os.makedirs(dst_root, exist_ok=True)

vasp_files = [f for f in os.listdir(src_dir) if f.endswith('.vasp')]

def label_from_choice(choice_dict):
    """把一次组合选择转成文件夹名，如 Hf→La__O→VAC"""
    parts = [f"{host}→{dop}" for host, dop in choice_dict.items()]
    return "__".join(parts)

for vfile in vasp_files:
    atoms0   = read(os.path.join(src_dir, vfile))
    basename = os.path.splitext(vfile)[0]

    # 收集每个母体元素在结构中的所有索引
    host_indices = {host: [i for i, a in enumerate(atoms0) if a.symbol == host]
                    for host in doping_plan}

    # 生成所有笛卡尔组合
    dopant_lists = doping_plan.values()          # e.g. (['La','Y'], ['VAC'])
    for dopant_choice in itertools.product(*dopant_lists):
        # dopant_choice 形如 ('La', 'VAC')
        choice_map   = {host: dop for host, dop in zip(doping_plan, dopant_choice)}
        scheme_label = label_from_choice(choice_map)

        # 对同一方案，可能有多个母体原子可选，需要遍历所有索引组合
        index_lists = [host_indices[host] for host in doping_plan]  # [[3,10],[7,15,20], …]
        for pick in itertools.product(*index_lists):
            # pick 是要真正动手的具体原子序号组合
            new_atoms = atoms0.copy()

            # 为了空位删除顺序正确，先把需要替换的原子索引倒排
            for (host, dop), idx in zip(choice_map.items(), pick):
                if dop == 'VAC':
                    new_atoms.pop(idx)           # 删掉母体原子
                else:
                    new_atoms[idx].symbol = dop  # 直接替换

            # 与当前方案已生成的结构做对称性去重
            folder = os.path.join(dst_root, basename, scheme_label)
            os.makedirs(folder, exist_ok=True)

            is_dup = False
            for exist_file in os.listdir(folder):
                ref = read(os.path.join(folder, exist_file))
                if comp.compare(new_atoms, ref):
                    is_dup = True
                    break
            if is_dup:
                continue

            # 写文件
            out_name = f"unique_{len(os.listdir(folder))}.vasp"
            write(os.path.join(folder, out_name), new_atoms)

print("Done! 结果已写入", dst_root)
```

## 如何修改脚本

- **仅修改 `doping_plan`.**

1. 只想把 Hf 全部替换成 Nb  
   ```python
   doping_plan = OrderedDict([('Hf', ['Nb'])])
   ```

2. 想在同一脚本里试 “Hf→La 或 Y”，同时再删一个 O  
   > 按需改动示例字典即可。

3. 再加一个 “Al→Ga” 掺杂  
   ```python
   doping_plan = OrderedDict([
       ('Hf', ['La', 'Y']),
       ('O',  ['VAC']),
       ('Al', ['Ga']),
   ])
   ```

运行  
```bash
python dopant_generator.py
```

## 结果层级

```
Results/
└─ <原 VASP 文件名>/
   ├─ Hf→La__O→VAC/
   │  └─ unique_0.vasp …
   └─ Hf→Y__O→VAC/
      └─ unique_0.vasp …
```

所有文件都做了同样操作，互不影响，方便后续计算。