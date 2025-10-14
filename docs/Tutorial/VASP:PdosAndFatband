# Tutorial: Calculating PDOS and Fatbands with VASP and pyband

## Introduction

This tutorial guides you through obtaining Projected Density of States (PDOS) and fatband structures using VASP and the `pyband` toolset. `pyband` provides convenient scripts (`pydos` and `pyband`) to visualize electronic structure data from VASP calculations.

## Prerequisites

- `pyband` toolset (clone from [https://github.com/QijingZheng/pyband](https://github.com/QijingZheng/pyband))
- Basic knowledge of VASP input files (INCAR, KPOINTS, POSCAR, POTCAR)

## Part 1: Preparing VASP Calculations

### 1.1 Structure Preparation

Create a POSCAR file with your desired crystal structure. Ensure proper formatting with lattice parameters and atomic coordinates.
### 1.2 INCAR Settings for SCF Calculation to Get a CHGCAR

Use these key parameters in your INCAR file:
```
LCHARG = True
NSW = 0
ICHARG = 2
ISMEAR = 0
```
KPOINTS:
```
Automatic mesh
0
Gamma
3 3 3            # k-point grid density
0  0  0             # Shift
```
### 1.3.1 INCAR Settings for PDOS Calculation (NSCF)

Use these key parameters in your INCAR file:

```
# Electronic structure settings
ISTART = 1          # Start from scratch
ICHARG = 11          # To obtain the eigenvalues (for band-structure plots) or the density of states (DOS) of a given charge density read from CHGCAR
LORBIT = 11         # Write orbitally resolved DOS (essential for PDOS)
ISMEAR = -5         #  Tetrahedron method
```
KPOINTS Settings for PDOS Calculation, more densed kpoints  

```
Automatic mesh
0
Gamma
10 10 10            # k-point grid density
0  0  0             # Shift
```
### 1.3.2 INCAR Settings for Fatband Calculation (NSCF)
Use these key parameters in your INCAR file:
```
ISTART = 1          # Start from scratch
ICHARG = 11          # To obtain the eigenvalues (for band-structure plots) or the density of states (DOS) of a given charge density read from CHGCAR
LORBIT = 11         # Write orbitally resolved DOS (essential for PDOS)
ISMEAR = -5         #  Tetrahedron method
```
Use a k-point path through high-symmetry points for band structures:

```
Line-mode
0
Reciprocal
10                  # Number of k-points per segment
Gamma  0.0 0.0 0.0
M      0.5 0.5 0.0
K      0.333 0.333 0.0
Gamma  0.0 0.0 0.0
```

## Part 2: Plotting PDOS with `pydos`

The `pydos` script visualizes partial density of states from VASP's PROCAR file.

### 2.1 Basic PDOS Plot

```bash
pydos -p '1 3 4' -x -1 2 -y 0 6 -z 0.65
```

- `-p '1 3 4'`: Specifies atom indices (1-based) to include in PDOS
- `-x -1 2`: Sets x-axis limits (energy range)
- `-y 0 6`: Sets y-axis limits (DOS intensity)
- `-z 0.65`: Sets energy reference (e.g., Fermi level)

### 2.2 Grouped Atom PDOS

Plot PDOS for multiple atom groups with different colors:

```bash
pydos -p '1 3 4' -p '2 7 8' -p '5 6 9' -z 0.65 -x -1 2 -y 0 6
```

This command creates a PDOS plot with three distinct groups of atoms, each represented by a different color.

### 2.3 Saving Output

By default, `pydos` generates a PNG image, and save file to a .dat file. To specify a custom filename:

```bash
pydos -p '1-4' -o my_pdos.png --tofile pdos.dat
```

## Part 3: Plotting Fatbands with `pyband`

Fatband plots show the contribution of specific atoms/orbitals to electronic bands using colored dots or lines.

### 3.1 Basic Fatband Plot

```bash
pyband --occ '1 3 4'
```

- `--occ '1 3 4'`: Shows contribution from atoms 1, 3, and 4
- Dots size represents the weight of specified atoms in each band

### 3.2 Orbital-Projected Fatbands

Include specific orbitals using the `--spd` flag:

```bash
pyband --occ '1 3 4' --spd 'd' -k mgkm
```

- `--spd 'd'`: Projects only d-orbitals (4-8 in VASP's orbital numbering)
- `-k mgkm`: Labels high-symmetry k-points on the x-axis

Orbital numbering in `pyband`:
- s orbital: 0
- p orbitals (py, pz, px): 1, 2, 3
- d orbitals (dxy, dyz, dz2, dxz, dx2): 4, 5, 6, 7, 8

### 3.3 Multiple Atom Groups with Colormap

```bash
pyband --occ '1 2' --occ '3 4 5 6' --occL -t --triAxesLabels Mo S Se -k mgkm
```

- `--occL`: Uses colormap instead of dot size
- `-t`: Enables transparency
- `--triAxesLabels`: Labels for each atom group

### 3.4 Custom Colors and Orbital Combinations

```bash
pyband --occ '3 4' --spd '1' --occMc 'red' --occ '3-4' --spd '2-3' --occMc 'blue'
```

- `--spd '1'`: p-orbital (py) projection
- `--spd '2-3'`: pz and px orbitals
- `--occMc`: Sets custom color for each group
