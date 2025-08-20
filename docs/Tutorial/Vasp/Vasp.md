以下内容为清理、重排后的 **Markdown** 版本


---

# VASP 流程

林子越

## 1. 准备文件

### 1.1 赝势 POTCAR

POTCAR 一般位于服务器 VASP 安装目录（如 `6001-ddf6/vasppp`）下，建议选用 **PBE** 赝势。
以 F 为例：

* `F`  普通赝势
* `F_s`  软赝势
* `F_h`  硬赝势
* `sv` / `pv`  表示价电子数不同

合并赝势示例（以 W₄S₈ 为例，仅需合并 W 与 S）：

```bash
cat POTCAR-W POTCAR-S > POTCAR
```

> 注意：最终文件名必须为 `POTCAR`。

### 1.2 结构文件 POSCAR

1. 将 `.cell` 文件导入 **VESTA** → 导出为 VASP 格式并重命名为 `POSCAR`。
2. 建议先用 **MS** 加对称性，减小胞参数：
   * Build → Symmetry → Primitive Cell
   * 若加对称性后胞反而变大，可先加对称性再转为原胞。

## 2. 产生 KPOINTS

将 `a.out createKpoints prodKpts.f90` 拷入与 `POSCAR` 同一目录：

```bash
chmod +x a.out
./a.out      # 生成 KPOINTS
```

## 3. 结构优化

### 3.1 所需文件

* `vasp.pbs`
* `POSCAR`
* `POTCAR`

### 3.2 `vasp.pbs` 脚本

```bash
#!/bin/bash
#PBS -q CT1
#PBS -l nodes=1:ppn=12
#PBS -j oe
#PBS -V
#PBS -N VASP-opt

cd "$PBS_O_WORKDIR"

for i in 30000    # 压力(kbar)，可写成 “1000 2000 3000 …” 计算多点
do
cat > INCAR << EOF
PSTRESS = $i
ISTART  = 0
ICHARG  = 2
IBRION  = 2
NSW     = 300
POTIM   = 0.1
NELM    = 60
EDIFF   = 1E-7
EDIFFG  = -0.005
ISMEAR  = 1
SIGMA   = 0.2
ISIF    = 3
ENCUT   = 550
PREC    = Accurate
LWAVE   = .FALSE.
LCHARG  = .TRUE.
NPAR    = 4
LORBIT  = 11
GGA     = PE
EOF

echo "pressure = $i kbar"

# ① 直接在脚本生成 KPOINTS
/public/home/YHY/lzy/Vasp/Gen_kpoints/a.out

# ② 若已手动生成 KPOINTS，可删除上一行

mpirun -np 12 /share/apps/compiler/VASP-5.3/vasp > log 2>&1

tail -1 OSZICAR                                         >> SUMMARY.dia
grep ' enthalpy is TOTEN' OUTCAR | tail -1              >> zToten.dia
grep 'volume of cell' OUTCAR    | tail -1              >> zVolum.dia
grep 'reached required accuracy - stopping' OUTCAR      >> zWork.dia

cp OUTCAR   outcar_$i
cp OSZICAR  oszicar_$i
cp CONTCAR  CONTCAR_$i
cp KPOINTS  KPOINTS_$i
cp CONTCAR  POSCAR           # 覆盖作下一轮起始结构
done

cat SUMMARY.dia zToten.dia zVolum.dia zWork.dia
```

### 3.3 输出

循环结束后，当前目录下的 `POSCAR` 即为优化后结构。

## 4. 静态自洽计算（SCF）

### 4.1 INCAR

```txt
SYSTEM = CoH
PREC   = Accurate
ENCUT  = 700
EDIFF  = 1E-5
ISTART = 0
ISMEAR = 1
SIGMA  = 0.2
```

### 4.2 脚本示例

```bash
#!/bin/bash
#PBS -q CT1
#PBS -l nodes=1:ppn=12
#PBS -j oe
#PBS -V
#PBS -N VASP-scf

cd "$PBS_O_WORKDIR"

for i in 30000      # 压力(kbar)
do
cat > INCAR << EOF
SYSTEM = F
PREC   = Accurate
ENCUT  = 550
EDIFF  = 1E-5
ISTART = 0
ISMEAR = 1
SIGMA  = 0.2
EOF

/public/home/YHY/lzy/Vasp/Gen_kpoints/a.out
mpirun -np 12 /share/apps/compiler/VASP-5.3/vasp > log 2>&1
done
```

完成后用

```bash
grep "E-fermi" OUTCAR
```

记录 ​**费米能级**​，供后续能带/态密度使用。

## 5. 非自洽计算——能带 (Band)

### 5.1 INCAR

```txt
SYSTEM  = CoH
PREC    = Accurate
ENCUT   = 700
ISTART  = 1
ICHARG  = 11
ISMEAR  = 1      # 半导体/绝缘体改 0  SIGMA=0.05
SIGMA   = 0.2
LWAVE   = .FALSE.
NBANDS  = 8      # 视需要加大
```

### 5.2 syml 文件示例

```txt
5
20 20 20 20
X 0.500 0.000 0.000
R 0.500 0.500 0.500
M 0.500 0.500 0.000
G 0.000 0.000 0.000
R 0.500 0.500 0.500
# 逆/倒格子基矢
0.000000000 1.840208159 1.840208159 0.271708392 0.271708392 0.271708392
1.840208159 0.000000000 1.840208159 0.271708392 -0.271708392 0.271708392
1.840208159 1.840208159 0.000000000 0.271708392 0.271708392 -0.271708392
-20 50
5.9036      # 费米能
```

### 5.3 生成高对称线 KPOINTS

在 `Genq_points` 目录执行

```bash
chmod +x a.out
./a.out      # 输出 inp.kpt
```

随后手动整理为 VASP `KPOINTS`，示例：

```txt
k-points along high symmetry lines
141
Reciprocal
0.000000 0.000000 0.000000 1.00
0.000000 0.000000 0.025000 1.00
...
-0.333000 0.667000 0.000000 1.00
```

### 5.4 运行脚本

```bash
#!/bin/bash
#PBS -q CT1
#PBS -l nodes=1:ppn=12
#PBS -j oe
#PBS -V
#PBS -N VASP-band

cd "$PBS_O_WORKDIR"
export PW_ROOT=/share/apps/compiler/VASP-5.3
mpirun -np 12 $PW_ROOT/vasp > log
```

完成后执行 `./a.out` 生成 `bnd.dat`，用 Origin 绘图。

> 提示：若出现
> `WARNING: small aliasing (wrap around) errors must be expected`
> 请提高 `ENCUT` 至 700–800 eV。

## 6. 非自洽计算——态密度 (DOS)

### 6.1 INCAR

```txt
SYSTEM = CoH
PREC   = Accurate
ENCUT  = 700
ISTART = 1
ICHARG = 11
ISMEAR = -5
LORBIT = 11
LWAVE  = .TRUE.
ALGO   = Fast
EDIFF  = 1E-5
NEDOS  = 3001
```

其余脚本同 5.4，完成后执行 `./a.out` 或 `./split.sh` 生成 `DOS_*`。

## 7. Bader 电荷

### 7.1 INCAR

```txt
SYSTEM = CoH
PREC   = Accurate
ENCUT  = 700
EDIFF  = 1E-5
ISTART = 0
ICHARG = 2
ISMEAR = 1
SIGMA  = 0.2
LWAVE  = .FALSE.
NGXF   = 192   # OUTCAR 对应值 ×4
NGYF   = 192
NGZF   = 192
LAECHG = .TRUE.
```

### 7.2 分析流程

```bash
chmod +x bader chgsum.pl
./chgsum.pl AECCAR0 AECCAR2
./bader CHGCAR -ref CHGCAR_sum
vi ACF.dat       # 查看电荷得失
```

## 8. 电子局域函数 ELF

### 8.1 INCAR

```txt
SYSTEM = CoH
PREC   = Accurate
ENCUT  = 700
EDIFF  = 1E-6
ISMEAR = 1
SIGMA  = 0.2
LWAVE  = .FALSE.
LCHARG = .TRUE.
LELF   = .TRUE.
NGX    = 48
NGY    = 48
NGZ    = 48
NPAR   = 4
```

计算结束得到 `ELFCAR`，加元素名后用 ​**VESTA**​：
Utilities → 2D Data Display → Slice (Max 1 / Min 0)。

## 9. Phonopy 声子谱 & DOS

### 9.1 INPHON-in

```txt
ATOM_NAME = F
DIM       = 1 1 1
PM        = .TRUE.
DIAG      = .FALSE.
```

### 9.2 INPHON-band

```txt
ATOM_NAME       = F
DIM             = 1 1 1
PM              = .TRUE.
DIAG            = .FALSE.
ND              = 4
FORCE_CONSTANTS = WRITE
NPOINTS         = 51
BAND = 0.500 0.000 0.000  0.500 0.500 0.500  0.500 0.500 0.000 \
       0.000 0.000 0.000  0.500 0.500 0.500
```

### 9.3 INPHON-dos

```txt
ATOM_NAME       = F
DIM             = 1 1 1
PM              = .TRUE.
DIAG            = .FALSE.
DOS_RANGE       = -20 90 0.1
FORCE_CONSTANTS = WRITE
MP              = 9 9 9
SIGMA           = 0.5
#PDOS = 1 2 3 4 5
```

### 9.4 计算步骤

```bash
phonopy --symmetry --tolerance=0.01 | head   # 检查对称性
phonopy -d INPHON-in                         # 生成位移超胞 POSCAR-***
```

随后使用下列脚本逐个超胞计算力：

```bash
#!/bin/bash
#PBS -q CT1
#PBS -l nodes=1:ppn=12
#PBS -j oe
#PBS -V
#PBS -N VASP-phonon

cd "$PBS_O_WORKDIR"

for i in 001 002 003 004 005 006
do
  cp POSCAR-$i POSCAR
  cat > INCAR << EOF
SYSTEM = Phon
ISTART = 0
ICHARG = 2
INIWAV = 1
NELMIN = 2
EDIFF  = 1E-5
EDIFFG = -0.005
NSW    = 0
IBRION = 8
ISMEAR = 0
SIGMA  = 0.05
ADDGRID= .TRUE.
ENCUT  = 550
PREC   = Accurate
IALGO  = 38
LREAL  = .FALSE.
LWAVE  = .FALSE.
LCHARG = .FALSE.
NPAR   = 4
EOF
  mpirun -np 12 /share/apps/compiler/VASP-5.3/vasp > log
  cp vasprun.xml vasprun.xml-$i
done
```

合并力常数并绘图：

```bash
phonopy -f vasprun.xml-00*
phonopy INPHON-band
phonopy-bandplot --gnuplot band.yaml > band.dat
phonopy --dos INPHON-dos            # total_dos.dat
```

## 10. COHP (LOBSTER)

### 10.1 INCAR

```txt
PREC   = Accurate
ENCUT  = 900
EDIFF  = 1E-7
EDIFFG = -1E-6
ISMEAR = -5
LREAL  = .FALSE.
NSW    = 0
ISIF   = 0
ISYM   = -1
NBANDS = 58
NPAR   = 4
NEDOS  = 801
LORBIT = 12
```

### 10.2 `lobsterin` 示例

```txt
COHPstartEnergy  -30
COHPendEnergy     30
basisSet          Bunge
includeOrbitals   spd
cohpGenerator     from 1.886 to 1.887 type F type Rb
```

### 10.3 运行

```bash
chmod +x lobster
./lobster
```

结果：

* `COHPCAR.lobster` 第 1 列能量，2–7 列依次为平均/积分及各近邻 COHP
* `ICOHPLIST.lobster` 给出各键 ICOHP 数值

---


