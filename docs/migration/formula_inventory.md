# 公式审计清单

以下内容逐字按原模块记录；本阶段未修改任何公式。来源字段只记录代码已有注释/数据库描述，未明确的标为“待核实”。

| 文件/函数 | 输入 | 输出 | 单位 | 当前公式/规则 | 代码来源 | 来源明确 |
|---|---|---|---|---|---|---|
| `carbon_calculator.py::calculate_direct_emissions` | 处理水量、进/出水 TN、COD | `N2O_emission`, `N2O_CO2eq` | kg N2O, kgCO2eq | `max(0,Q*(TNin-TNout)*0.016*(44/28)/1000)`；`N2O*273` | `EF_N2O=0.016`, `C_N2O_N2=44/28`, 因子库 N2O/IPCC AR6 | 部分明确；0.016 待核实 |
| 同上 | 处理水量、进/出水 COD | `COD_removed`, `CH4_emission`, `CH4_CO2eq` | kg COD, kg CH4, kgCO2eq | `max(0,Q*abs(CODin-CODout)/1000)`；`COD_removed*B0*MCF`；`CH4*27.9` | `B0=0.25`, `MCF=0.003`, 因子库 CH4/IPCC AR6 | GWP 明确；B0/MCF 待核实 |
| `calculate_indirect_emissions` | 电耗、PAC/PAM/次氯酸钠/臭氧 | 各 CO2eq、`chemicals_CO2eq` | kgCO2eq | `max(0,用量*排放因子)`；药剂四项求和 | 因子库默认值和数据库描述 | 因子值有描述；部分研究文献待核实 |
| `calculate_unit_emissions` | 能耗、直接排放、药耗、处理水量 | 六区排放、总排放、碳效率 | kgCO2eq, m3/kgCO2eq | 预处理=`energy*0.3193`; 生物=`N2O+CH4+energy*0.4453`; 深度=`chemicals+energy*0.1155`; 泥=`energy*0.0507`; 出水=`energy*0.0672`; 除臭=`energy*0.0267`; 总和；`Q/total` | `energy_distribution` 代码常量 | 否，待核实 |
| `calculate_carbon_offset` | COD_removed、电耗、日期行数、污泥外运量、技术 | 技术抵消量 | kgCO2eq | 沼气=`COD_removed*0.3*2*2.5`; 光伏=`100*4*len(df)*0.85`; 热泵=`sum(电耗)*0.1*1.2`; 污泥=`sum(外运量)*0.8*0.3` | 原函数注释、因子库研究文献 | 公式假设待核实 |
| `calculate_carbon_reduction_metrics` | 单元排放、处理水量、技术 | 总/净排放、效率、能源中和率、减排率 | kgCO2eq, m3, % | 净排放=`max(0,total-offset)`；能源产出=`biogas_power + 100*4*len(df)`（光伏）；中和率=min(产出/电耗,1)*100；减排率=`offset/total*100` | 原函数 | 否，待核实 |
| `optimize_parameters` | 数据、目标减排率 | 四种策略结果 | kgCO2eq, % | 曝气能耗 -15%、回流能耗 -5%、药剂 -20%、综合能耗 -10%/药剂 -15%；N2O 策略将出水 TN 乘 0.9；复算排放 | 原函数策略字典 | 否，待核实 |
| `compare_carbon_techs` | 技术列表、可选数据/水量 | 技术对比表 | kgCO2eq, 万元, 年, % | 技术减排率 5%-25%；投资=`总水量*investment_per_m3/10000`；能源中和率=`min(50,reduction_rate*150)` | 原函数注释 | 否，待核实 |
| `DataSimulator` 生成函数 | 日期长度、随机噪声 | 水量、能耗、药耗、水质 | 原始单位 | 正弦季节项、线性趋势、正态噪声；能耗=`水量*(0.3+季节+噪声)`；药剂比例 PAC 0.02、PAM 0.005、次氯酸钠 0.01；最后调用碳核算 | 原模块注释 | 参数说明存在；科学来源待核实 |
| `lstm_predictor._enhanced_fallback_predict` / `CarbonCalculator._simple_emission_prediction` | 历史排放、预测步数 | 预测值、上下限 | kgCO2eq | 统计均值、线性趋势、正弦季节、随机噪声；值裁剪到均值 0.5-1.5 倍 | 原函数注释 | 否，待核实 |

## 因子来源待核实项

- 电力 2020-2022：数据库描述为生态环境部公告 2023/2024 年份文件。
- N2O/CH4 GWP：IPCC AR6；代码未绑定具体表格页码。
- PAC/PAM/次氯酸钠：`T/CAEPI 49-2022`；臭氧和四类抵消因子仅写“研究文献”。
- B0、MCF、EF_N2O、能耗分配比例、技术比例和预测假设均没有可验证引用，统一标记“待核实”。

