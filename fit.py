import argparse
import numpy as np
import json
import time
import optuna
from model import Model, BaseModel
import simulate
import logs

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--logdir", type=str, required=True)
arg_parser.add_argument("--output", type=str, default="params.json")
arg_parser.add_argument("--trials", type=int, default=10000)
arg_parser.add_argument("--jobs", type=int, default=1)
args = arg_parser.parse_args()

logs = logs.Logs(args.logdir)


def compute_score(model: BaseModel, log: dict) -> float:
    simulator = simulate.Simulate1R(log["mass"], log["length"], model)
    positions = simulator.rollout_log(log)
    log_positions = np.array([entry["position"] for entry in log["entries"]])

    return np.mean(np.abs(positions - log_positions))


def compute_scores(model: BaseModel):
    scores = 0
    for log in logs.logs:
        # t0 = time.time()
        scores += compute_score(model, log)
        # t1 = time.time()
        # elapsed = t1 - t0
        # print(f"Durations: {elapsed:.6f} s")

    return scores / len(logs.logs)


def objective(trial):
    model = Model()
    parameters = model.get_parameters()
    for name in parameters:
        parameter = parameters[name]
        if parameter.optimize:
            parameter.value = trial.suggest_float(name, parameter.min, parameter.max)

    return compute_scores(model)


sampler = optuna.samplers.CmaEsSampler()
study = optuna.create_study(sampler=sampler)
study.optimize(objective, n_trials=args.trials, n_jobs=args.jobs)

json.dump(study.best_params, open(args.output, "w"))

print()
print("Done, best params found: ")
for key in study.best_params:
    print(f"- {key}: {study.best_params[key]}")
