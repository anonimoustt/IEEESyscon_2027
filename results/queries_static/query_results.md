### Q1_model_information (8 rows)

| relation | value | type |
|---|---|---|
| has_configuration | MLP_Weather_Hyperparameters | Hyperparameter_Configuration |
| has_configuration | MLP_Weather_Training | Training_Configuration |
| implements_algorithm | Multilayer_Perceptron | Deep_Learning_Algorithm |
| implements_algorithm | Multilayer_Perceptron | Supervised_Algorithm |
| operates_on_context | Weather_Years_11_to_50 | Operational_Context |
| suited_for_context | NOAA_Daily_Weather_Records | Data_Characteristics |
| suited_for_context | Rain_Prediction | Problem_Context |
| suited_for_context | Weather_Years_6_to_10 | Operational_Context |

### Q2_monitoring_settings (1 rows)

| algorithm | seed | hiddenUnits | maxIter | trainFrom | trainTo | commFrom | commTo | opFrom | opTo | task | parameters | checkDays | blockDays | validationYears | epsilon | pct | pctSevere | sigma | refSize | resampleSizes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Multilayer_Perceptron | 0 | 16 | 3000 | 1 | 5 | 6 | 10 | 11 | 50 | binary classification: rain or no rain | 161 | 360 | 30 | 5000 | 0.1 | 95 | 99 | 0.1 | 1000 | 400,800,200,1600 |

### Q3_monitoring_plan (14 rows)

| metric | attribute | link |
|---|---|---|
| Accuracy | Correctness | direct |
| Accuracy_Variance | Correctness | direct |
| Accuracy_Variance | Reliability | direct |
| Attack_Success_Rate | Security | direct |
| Explanation_Fidelity | Transparency_Interpretability | direct |
| Explanation_Stability | Predictability | direct |
| Explanation_Stability | Transparency_Interpretability | direct |
| F1_Score | Correctness | direct |
| KS | Reliability | direct |
| KS | Resilience | severe shift only |
| MMD | Reliability | direct |
| MMD | Resilience | severe shift only |
| Prediction_Flip_Rate | Predictability | direct |
| Unsafe_Output_Rate | Safety | direct |

### Q4_inapplicable_metrics (2 rows)

| model | metric | algorithm |
|---|---|---|
| LR_Weather | Explanation_Stability | Logistic_Regression |
| LR_Weather | Explanation_Fidelity | Logistic_Regression |

### Q5_blind_spots (1 rows)

| model | attribute |
|---|---|
| LR_Weather | Transparency_Interpretability |

### Q6_detectable_debts (10 rows)

| model | debt |
|---|---|
| LR_Weather | Capability_Loss |
| LR_Weather | Harmful_Output |
| LR_Weather | Operating_Envelope |
| LR_Weather | Robustness_Debt |
| MLP_Weather | Capability_Loss |
| MLP_Weather | Faithfulness |
| MLP_Weather | Harmful_Output |
| MLP_Weather | Operating_Envelope |
| MLP_Weather | Robustness_Debt |
| MLP_Weather | Source_Target_Mismatch |

### Q7_debt_definitions (13 rows)

| debt | attribute | provenance |
|---|---|---|
| Capability_Loss | Correctness | Fine_Tuning_Configuration |
| Capability_Loss | Reliability | Fine_Tuning_Configuration |
| Faithfulness | Predictability |  |
| Faithfulness | Transparency_Interpretability |  |
| Harmful_Output | Safety |  |
| Harmful_Output | Security |  |
| Operating_Envelope | Reliability |  |
| Operating_Envelope | Resilience |  |
| Robustness_Debt | Correctness |  |
| Robustness_Debt | Security |  |
| Source_Target_Mismatch | Predictability | Transfer_Configuration |
| Source_Target_Mismatch | Reliability | Transfer_Configuration |
| Source_Target_Mismatch | Transparency_Interpretability | Transfer_Configuration |

### Q8_thresholds (0 rows)

| metric | tau | tauSevere |
|---|---|---|

### Q9_case_degraded_attributes (9 rows)

| model | attribute | metric |
|---|---|---|
| ALINA_on_Runways | Correctness | Accuracy |
| ALINA_on_Runways | Reliability | MMD |
| ALINA_on_Runways | Safety | Unsafe_Output_Rate |
| AssistTaxi_Lane_Detector | Correctness | F1_Score |
| AssistTaxi_Lane_Detector | Reliability | MMD |
| Language_Model_Composite | Correctness | Performance_Drift_Rate |
| Language_Model_Composite | Reliability | Performance_Drift_Rate |
| Language_Model_Composite | Safety | Unsafe_Output_Rate |
| Language_Model_Composite | Security | Attack_Success_Rate |

### Q10_case_active_debts (4 rows)

| model | debt | support |
|---|---|---|
| AssistTaxi_Lane_Detector | Capability_Loss | 2 |
| Language_Model_Composite | Capability_Loss | 1 |
| Language_Model_Composite | Harmful_Output | 2 |
| Language_Model_Composite | Robustness_Debt | 2 |

### Q11_signatures_without_provenance (1 rows)

| model | debt |
|---|---|
| ALINA_on_Runways | Capability_Loss |

### Q12_failure_path (0 rows)

| metric | attribute | document |
|---|---|---|

