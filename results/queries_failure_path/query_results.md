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
| Multilayer_Perceptron | 0 | 16 | 3000 | 1 | 5 | 6 | 10 | 11 | 50 | binary classification: rain or no rain | 161 | 360 | 30 | 5000 | 0.1 | 95 | 99 | 0.1 | 1000 | 400,200,800,1600 |

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

### Q8_thresholds (10 rows)

| metric | tau | tauSevere |
|---|---|---|
| Accuracy | 0.2270833333333333 | 0.2451388888888889 |
| Accuracy_Variance | 0.0736019104235915 | 0.08966570211550043 |
| Attack_Success_Rate | 0.40555555555555556 | 0.44861111111111107 |
| Explanation_Fidelity | 0.35635220198912076 | 0.3950324784367373 |
| Explanation_Stability | 0.011041549868159778 | 0.011865876937117742 |
| F1_Score | 0.48153926786002255 | 0.526785728920495 |
| KS | 0.32116666666666666 | 0.37955555555555553 |
| MMD | 0.0689808895357363 | 0.11308261469792971 |
| Prediction_Flip_Rate | 0.08333333333333333 | 0.09583333333333333 |
| Unsafe_Output_Rate | 0.5956960063147657 | 0.6411334735537232 |

### Q9_case_degraded_attributes (12 rows)

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
| MLP_Weather | Correctness | Accuracy |
| MLP_Weather | Reliability | KS |
| MLP_Weather | Security | Attack_Success_Rate |

### Q10_case_active_debts (5 rows)

| model | debt | support |
|---|---|---|
| AssistTaxi_Lane_Detector | Capability_Loss | 2 |
| Language_Model_Composite | Capability_Loss | 1 |
| Language_Model_Composite | Harmful_Output | 2 |
| Language_Model_Composite | Robustness_Debt | 2 |
| MLP_Weather | Robustness_Debt | 2 |

### Q11_signatures_without_provenance (2 rows)

| model | debt |
|---|---|
| MLP_Weather | Capability_Loss |
| ALINA_on_Runways | Capability_Loss |

### Q12_failure_path (6 rows)

| metric | attribute | document |
|---|---|---|
| Accuracy | Correctness | EASA_ML_Concept_Paper |
| Accuracy | Correctness | EU_AI_Act |
| Accuracy | Correctness | NIST_AI_RMF |
| Attack_Success_Rate | Security | EASA_ML_Concept_Paper |
| Attack_Success_Rate | Security | EU_AI_Act |
| Attack_Success_Rate | Security | NIST_AI_RMF |

