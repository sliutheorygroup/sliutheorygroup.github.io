import numpy as np
from scipy.optimize import curve_fit

# 定义三阶Birch-Murnaghan状态方程函数
def birch_murnaghan_3rd_order(V, E0, V0, B0, B0p):
    """
    V: 体积
    E0: 平衡能量
    V0: 平衡体积
    B0: 体弹模量
    B0p: B0对压力的一阶导数
    返回给定体积V下的能量
    """
    V = np.array(V) # 确保V是数组
    # 避免除零或负体积，必要时可加判断
    eta = (V0 / V) ** (2/3)
    return E0 + (9 * V0 * B0 / 16) * ( (eta - 1)**3 * B0p + (eta - 1)**2 * (6 - 4*eta) )

# 你的数据：假设volumes和energies是列表或数组
volumes = [...] # 填入你的体积数据列表
energies = [...] # 填入你的能量数据列表

# 初始猜测值 [E0, V0, B0, B0p]
# 注意：根据你的数据调整初始值！初始值离真值太远可能导致拟合失败。
p0 = [min(energies), volumes[np.argmin(energies)], 100, 4.0] # 示例初始值

# 进行曲线拟合
popt, pcov = curve_fit(birch_murnaghan_3rd_order, volumes, energies, p0=popt, maxfev=10000)
# popt是最优参数数组 [E0_opt, V0_opt, B0_opt, B0p_opt]
# pcov是参数的协方差矩阵，可用于计算标准差误差

E0_opt, V0_opt, B0_opt, B0p_opt = popt

# 计算拟合参数的标准误差
perr = np.sqrt(np.diag(pcov)) # 参数的标准误差

print(f"拟合结果:")
print(f"E0 = {E0_opt:.9f} ± {perr[0]:.9f}")
print(f"V0 = {V0_opt:.6f} ± {perr[1]:.6f}")
print(f"B0 = {B0_opt:.6f} ± {perr[2]:.6f} GPa")
print(f"B0' = {B0p_opt:.6f} ± {perr[3]:.6f}")

# 你可以用最优参数生成拟合曲线，用于绘图
V_fit = np.linspace(min(volumes), max(volumes), 1000)
E_fit = birch_murnaghan_3rd_order(V_fit, *popt)