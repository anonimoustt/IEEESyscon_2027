# Reproduces every result of the paper in about four minutes (Linux, macOS, Windows, or Google Colab).
# Usage: python run_all.py [DATA_DIR]     (default DATA_DIR: data/weather, downloaded if missing)
import os  # paths
import subprocess  # run each step
import sys  # interpreter and arguments

ROOT = os.path.dirname(os.path.abspath(__file__))  # repository folder
os.chdir(ROOT)  # every path below is relative to it
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "weather")  # weather data folder
PY = sys.executable  # the same Python that runs this script
STATIC = os.path.join("ontology", "trustworthiness_debt.owl")  # static ontology
WITH_TH = os.path.join("ontology", "trustworthiness_debt_with_thresholds.owl")  # ontology after thresholds are set
MON = os.path.join("results", "monitor")  # monitor outputs
FIG = os.path.join("results", "figures")  # figures
os.makedirs(FIG, exist_ok=True)  # create the figure folder

STEPS = [  # (description, command)
    ("download and check the weather data", [PY, "code/download_weather.py", DATA]),  # NOAA data
    ("build the static ontology", [PY, "code/build_static_ontology.py", "ontology"]),  # OWL file
    ("run the SPARQL queries Q1 to Q12", [PY, "code/run_queries.py", STATIC, "queries", "results/queries_static"]),  # tables
    ("run the DL queries D1 to D7 with HermiT", [PY, "code/run_dl_queries.py", STATIC, "results/dl_queries.json"]),  # reasoner
    ("monitor the network", [PY, "code/ontology_monitor.py", STATIC, "queries", DATA, "MLP_Weather", MON, WITH_TH]),  # monitor
    ("monitor the logistic regression", [PY, "code/ontology_monitor.py", WITH_TH, "queries", DATA, "LR_Weather", MON,  # monitor
                                         WITH_TH]),  # adds its thresholds to the same file
    ("independent check, network", [PY, "code/weather_debt_check.py", DATA, MON, "MLP_Weather",  # no ontology
                                    os.path.join(MON, "cross_check_MLP_Weather.json")]),  # report
    ("independent check, logistic regression", [PY, "code/weather_debt_check.py", DATA, MON, "LR_Weather",  # no ontology
                                                os.path.join(MON, "cross_check_LR_Weather.json")]),  # report
    ("run the SPARQL queries on the ontology with thresholds", [PY, "code/run_queries.py", WITH_TH, "queries",  # Q8 filled
                                                                "results/queries_with_thresholds"]),  # output folder
    ("record year 21 of the network for Protege", [PY, "code/failure_path.py", WITH_TH,  # failure path demo
                                                   os.path.join(MON, "monitor_years_MLP_Weather.csv"), "MLP_Weather", "21",  # year 21
                                                   os.path.join("ontology", "failure_path_MLP_Weather_year21.owl")]),  # separate file
    ("run the SPARQL queries on the record of year 21", [PY, "code/run_queries.py",  # Q12 filled
                                                         os.path.join("ontology", "failure_path_MLP_Weather_year21.owl"),  # demo file
                                                         "queries", "results/queries_failure_path"]),  # output folder
    ("draw the figure of the 40 monitored years", [PY, "code/fig_weather.py", MON, "results/queries_static", os.path.join(FIG, "weather.pdf")]),  # figure
    ("compute the numbers of Section IV", [PY, "code/paper_numbers.py", MON, "results/paper_numbers.json", DATA]),  # numbers
]  # end of the step list

for i, (what, cmd) in enumerate(STEPS, 1):  # each step in order
    print("[%d/%d] %s" % (i, len(STEPS), what), flush=True)  # progress
    out = subprocess.run(cmd, capture_output=True, text=True)  # run it
    if out.returncode != 0:  # the step failed
        print(out.stdout, out.stderr)  # show what went wrong
        sys.exit("step %d failed: %s" % (i, what))  # stop here
print("done: results are in results/, the figure in results/figures/weather.png")  # finished
