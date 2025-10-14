# Dynamic BEC in LAMMPS
introduction !!!

## Prerequisites

- sklearn, pandas, numpy
- LAMMPS

## The displacement-BEC relationship is fitted using machine learning methods with polynomial and cosine features to model BEC as a function of in-plane displacement.

```
import pandas as pd
import numpy as np
from sklearn.linear_model import Lasso
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

# 假设我们已经加载了数据
data_path = 'all_Bdn_Z31.dat'  # 根据实际情况调整路径
data = pd.read_csv(data_path, sep='\s+', header=None, names=['a_x', 'a_y', 'b_x', 'b_y'])

# 从矢量a到矢量b的映射关系，我们先尝试找到a到b_x的映射
X0 = data[['a_x', 'a_y']]
y = data['b_y']  # 假设我们此次关注b_x

# 添加正弦和余弦特征
X = pd.DataFrame()
X['v_Bdnx'] =X0['a_x']
X['v_Bdny'] = X0['a_y']
X['cos(2*v_Bdnx)'] = np.cos(X0['a_x']*2)
X['cos(2*v_Bdny)'] = np.cos(X0['a_y']*2)

# 分割数据集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=5)

# 使用PolynomialFeatures生成多项式特征
poly = PolynomialFeatures(degree=3, include_bias=False)
X_train_poly = poly.fit_transform(X_train)
X_test_poly = poly.transform(X_test)

# 使用Lasso回归进行特征选择
lasso = Lasso(alpha=3e-5)  # 调整alpha以控制正则化强度
lasso.fit(X_train_poly, y_train)

# 使用模型进行预测
y_pred = lasso.predict(X_test_poly)
# 计算预测误差
mse = mean_squared_error(y_test, y_pred)
#rmse = np.sqrt(mse)
print(f'MSE: {mse}')
print('Intercept:', lasso.intercept_)
print('Coefficients:', lasso.coef_)

# 筛选出重要特征
important_indices = np.where(lasso.coef_ != 0)[0]
important_features = np.array(poly.get_feature_names_out())[important_indices]
important_coefficients = lasso.coef_[important_indices]

print('Important Features and their Coefficients:')
formula=""
for feature, coef in zip(important_features, important_coefficients):
	print(f'{feature}: {coef}')
	formula += f"+({coef:.4f}*{feature})"
print(formula)

```

## Implementation of a new LAMMPS command to compute vectors between two atoms for a given cutoff distance. 

```
cd lammps/src
cp compute_coord_atom.h compute_coordxmax_atom.h
vim compute_coordxmax_atom.h

```
![revised compute_coord_atom.h (left) to get a compute_coordxmax_atom.h (right)](./vimdiff_h.png)
```
cp compute_coord_atom.cpp compute_coordxmax_atom.cpp
vim compute_coordxmax_atom.cpp
```
![revised compute_coord_atom.cpp (left) to get a compute_coordxmax_atom.cpp (right)](./vimdiff1_cpp.png)
![revised compute_coord_atom.cpp (left) to get a compute_coordxmax_atom.cpp (right)](./vimdiff2_cpp.png)


### LAMMPS Installation [URL]

## Dynamic Born effective charge simulation in LAMMPS
### In-plane atomic displacement calculation
use the compute command to calculate the vector between two atoms for specified cutoff.
The vector is the displacement vector from the atom in group Bdn to the atom in group Nup.

```
compute Bdnx_tot Bdn coordxmin/atom cutoff 4 group Nup  #  the vector from Bdn to Nup in x direction for Bdn which Nup has the minmun distance in cutoff 4 A 
```
### Calculate the in-plane force from the in-plane displacement using the displacement-BEC relationship.
```
variable Bdnfy atom -${VALUEZ}*((-0.0055*sin(2*v_Bdnx))+(-0.005*v_Bdnx*v_Bdny)+(0.004*v_Bdnx*cos(2*v_Bdny))+(0.01*v_Bdny*sin(2*v_Bdnx))+(-0.0096*sin(2*v_Bdnx)*cos(2*v_Bdny))+(0.003*v_Bdnx^2*sin(2*v_Bdnx))+(-0.001*v_Bdnx*v_Bdny*cos(2*v_Bdny))+(0.002*v_Bdny*sin(2*v_Bdnx)*cos(2*v_Bdny))+(0.0009*sin(2*v_Bdnx)*cos(2*v_Bdny)^2))
```
### To optimize computational efficiency, we calculate the BEC every 50 simulation steps.

```
variable freq equal 50

fix ffB B store/state ${freq} v_Bdnfx v_Bdnfy v_Bupfx v_Bupfy
variable vffBdnx atom f_ffB[1]
variable vffBdny atom f_ffB[2]
variable vffBupx atom f_ffB[3]
variable vffBupy atom f_ffB[4]
```

## The complete input file for dynamic BEC simulation in LAMMPS
```
#Bilayer-BN
variable        TEMP            equal 300.000
variable        PRES            equal 1.01325
variable        TAU_T           equal 0.10000
variable        TAU_P           equal 0.50000
variable atomnum equal count(all)

units           metal
boundary        p p p
atom_style      atomic

neighbor        0.0 bin
neigh_modify every 10 delay 0 check yes

box          tilt large
read_data    ./conf.lmp 
change_box   all triclinic
mass            1 10.8
mass            2 14.0
pair_style      deepmd /storage/liushiLab/kechangming/P1_BN_sliding_EF/lmp/frozen_model_compressed.pb
pair_coeff     * * 

group   B  type 1
group   N  type 2

velocity        all create ${TEMP} 46955

variable Bdn_h equal ${atomnum}/4
variable Bup_h equal ${Bdn_h}*2
variable Ndn_h equal ${Bdn_h}*3  # 
variable Nup_h equal ${Bdn_h}*4  # 

variable Bdn_l equal 1
variable Bup_l equal ${Bdn_h}+1
variable Ndn_l equal ${Bdn_h}*2+1
variable Nup_l equal ${Bdn_h}*3+1

group Bdn id ${Bdn_l}:${Bdn_h}
group Bup id ${Bup_l}:${Bup_h}
group Ndn id ${Ndn_l}:${Ndn_h}
group Nup id ${Nup_l}:${Nup_h}

#variable VALUEX  equal 0.0
#variable VALUEY  equal 0.0
variable VALUEZ  equal 0.03 # the value of oop electric field
#============================ B sliding vector ============================================================
compute Bdnx_tot Bdn coordxmin/atom cutoff 4 group Nup  # the cutoff is the distance. coordx of Bdn minus coordx of Nup
compute Bdny_tot Bdn coordymin/atom cutoff 4 group Nup
variable Bdny atom c_Bdnx_tot
variable Bdnx atom -c_Bdny_tot

compute Bupx_tot Bup coordxmin/atom cutoff 4 group Ndn #obtain of the x vector of the minimum bonds, the direction is N point to B
compute Bupy_tot Bup coordymin/atom cutoff 4 group Ndn
variable Bupy atom c_Bupx_tot
variable Bupx atom -c_Bupy_tot

#============================= electric field induced force in BN plane coordination =============================
variable Bdnfy atom -${VALUEZ}*((-0.0055*sin(2*v_Bdnx))+(-0.005*v_Bdnx*v_Bdny)+(0.004*v_Bdnx*cos(2*v_Bdny))+(0.01*v_Bdny*sin(2*v_Bdnx))+(-0.0096*sin(2*v_Bdnx)*cos(2*v_Bdny))+(0.003*v_Bdnx^2*sin(2*v_Bdnx))+(-0.001*v_Bdnx*v_Bdny*cos(2*v_Bdny))+(0.002*v_Bdny*sin(2*v_Bdnx)*cos(2*v_Bdny))+(0.0009*sin(2*v_Bdnx)*cos(2*v_Bdny)^2))
variable Bdnfx atom ${VALUEZ}*(-0.00285-0.0046*v_Bdny-0.002*cos(2*v_Bdnx)+(0.0046*cos(2*v_Bdny))+(0.0014*v_Bdnx^2)-0.007*v_Bdny*cos(2*v_Bdnx)-0.0075*v_Bdny*cos(v_Bdny*2)+(0.002*cos(v_Bdny*2)^2)+(0.0019*v_Bdny^3)+(0.0026*v_Bdny^2*cos(v_Bdnx*2))-0.0016*v_Bdny*cos(v_Bdnx*2)^2-0.003*v_Bdny*cos(v_Bdnx*2)*cos(v_Bdny*2)-0.0013*v_Bdny*cos(v_Bdny*2)^2-0.0019*cos(v_Bdnx*2)^2*cos(v_Bdny*2))

variable Bupfy atom ${VALUEZ}*((-0.0055*sin(2*v_Bupx))+(-0.005*v_Bupx*v_Bupy)+(0.004*v_Bupx*cos(2*v_Bupy))+(0.01*v_Bupy*sin(2*v_Bupx))+(-0.0096*sin(2*v_Bupx)*cos(2*v_Bupy))+(0.003*v_Bupx^2*sin(2*v_Bupx))+(-0.001*v_Bupx*v_Bupy*cos(2*v_Bupy))+(0.002*v_Bupy*sin(2*v_Bupx)*cos(2*v_Bupy))+(0.0009*sin(2*v_Bupx)*cos(2*v_Bupy)^2))

variable Bupfx atom -${VALUEZ}*(-0.0028-0.0046*v_Bupy-0.002*cos(2*v_Bupx)+(0.0046*cos(2*v_Bupy))+(0.0014*v_Bupx^2)-0.007*v_Bupy*cos(2*v_Bupx)-0.0075*v_Bupy*cos(v_Bupy*2)+(0.002*cos(v_Bupy*2)^2)+(0.0019*v_Bupy^3)+(0.0026*v_Bupy^2*cos(v_Bupx*2))-0.0016*v_Bupy*cos(v_Bupx*2)^2-0.003*v_Bupy*cos(v_Bupx*2)*cos(v_Bupy*2)-0.0013*v_Bupy*cos(v_Bupy*2)^2-0.0019*cos(v_Bupx*2)^2*cos(v_Bupy*2))
#============================== add force ================================================

variable freq equal 50

fix ffB B store/state ${freq} v_Bdnfx v_Bdnfy v_Bupfx v_Bupfy
variable vffBdnx atom f_ffB[1]
variable vffBdny atom f_ffB[2]
variable vffBupx atom f_ffB[3]
variable vffBupy atom f_ffB[4]

compute Bdnxsum Bdn reduce sum v_vffBdnx
compute Bdnysum Bdn reduce sum v_vffBdny
#compute Bdnzsum Bdn reduce sum v_vffBdnz

compute Bupxsum Bup reduce sum v_vffBupx
compute Bupysum Bup reduce sum v_vffBupy
#compute Bupzsum Bup reduce sum v_vffBupz

variable xforce equal -(c_Bdnxsum+c_Bupxsum)/${atomnum}*2 # compensation force
variable yforce equal -(c_Bdnysum+c_Bupysum)/${atomnum}*2
#variable zforce equal -(c_Bdnzsum+c_Bupzsum)/${atomnum}*2

#fix ffcompens B ave/time ${freq} 1 ${freq} v_xforce v_yforce v_zforce

fix             fBdn  Bdn addforce v_vffBdnx v_vffBdny 0
fix             fBup  Bup addforce v_vffBupx v_vffBupy 0
fix             fcompens B addforce v_xforce v_yforce 0 # add compensation force
thermo          500
thermo_style    custom step pe ke etotal temp press vol cella cellb cellc cellalpha cellbeta cellgamma
dump 1 all custom 500 ef.lammpstrj id type x y z #v_vffBdn[1] v_vffBdn[2] v_vffBdn[3]
timestep       0.001
fix             2 all nvt temp ${TEMP} ${TEMP} ${TAU_T}

run 100000

#===================================  fix region ===============================================================================
#region fix_region1 block INF INF 0 15 INF INF
#region fix_region2 block INF INF 673 688 INF INF
#group gfix1 region fix_region1
#group gfix2 region fix_region2
#fix fixed1 gfix1 setforce 0 0 0
#fix fixed2 gfix2 setforce 0 0 0
#velocity gfix1 set 0 0 0
#velocity gfix2 set 0 0 0
#variable addfx atom fx-v_fx_ori
#variable addfy atom fy-v_fy_ori
#variable addfz atom fz-v_fz_ori

#dump 10 all custom 500 ef.lammpstrj id type x y z v_Bdnfx v_Bdnfy v_Bdnfz v_Bupfx v_Bupfy v_Bupfz v_sigma v_Bdnfx_rot v_Bdnfy_rot v_Bdnfz_rot v_Bupfx_rot v_Bupfy_rot v_Bupfz_rot

#dump            2 all custom 1000 ele_efield${VALUEZ}.lammpstrj id element x y z
#dump_modify 1 sort 1 element B N
#unfix 1
#run 500 pre no post no every 500 "include update_variables"
#label loop
#variable step loop 100

#include update_variables
#run 1 pre no post no
#variable mod equal ${step}%30
#if "${mod} == 0" then "include update_variables"unfix fBdn
#unfix fBup
#unfix fcompens
#unfix 1
#
#fix             fBdn  Bdn addforce v_Bdnfx_rot v_Bdnfy_rot v_Bdnfz_rot
#fix             fBup  Bup addforce v_Bupfx_rot v_Bupfy_rot v_Bupfz_rot
#fix             fcompens B addforce v_xforce v_yforce v_zforce # add compensation force
#
#fix             1 all nvt temp ${TEMP} ${TEMP} ${TAU_T}
#next step

write_data   struct.final


```
