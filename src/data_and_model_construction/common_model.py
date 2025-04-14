# Import libs
import sys
from docplex.mp.model import Model
from docplex.mp.constants import ComparisonType
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

from data_related_utils import BIG_M

#def load_data():
from .data import unpack_data

# Create the model with constraints and objective
def create_model(data_dict):
    name, products, resources, consumptions = unpack_data(data_dict)
    mdl = LpProblem(name, LpMaximize)
    #mdl = Model(name)

    prod_names = [prod[0] for prod in products]
    production_vars = {name: LpVariable(name, lowBound=0, cat='Continuous') for name in prod_names}

    # --- constraints ---
    # IMPORTANT: KEEP this format and naming convention, if you'll want to use plot_kind/* later (VM, CostoOp, etc).
    # resources disp equipo and consumptions
    for res in resources:
        constraint_name = f'Disp_{res[0]}'
        mdl += (
            lpSum(production_vars[p[0]] * consumptions[res[0]][products.index(p)] for p in products) <= res[1],
            constraint_name
        )
    # max demand
    for p in products:
        constraint_name = f'DemandMax_{p[0]}'
        mdl += (production_vars[p[0]] <= p[2], constraint_name)

    # min demand
    for p in products:
        constraint_name = f'DemandMin_{p[0]}'
        mdl += (production_vars[p[0]] >= p[3], constraint_name)

    # --- print information ---
    print(f"Modelo: {mdl.name}")
    print(f"Cantidad de variables: {len(mdl.variables())}")
    print(f"Cantidad de restricciones: {len(mdl.constraints)}")

    total_benefit = lpSum(production_vars[p[0]] * p[1] for p in products)


    # --- set the objective ---
    mdl += total_benefit, "Maximize_Benefit"


    # IMPORTANT: KEEP these three variables, if you'll want to use plot_kind/* later.
    return mdl, production_vars, products

# Print model human friendly name, restrictions and objective.
# Do not print restrictions such as ">=0" nor "<= inf".
def print_model(mdl):
    print("--------------------")
    print(f"Model: {mdl.name}")

    print("Constraints:")

    # Print all constraints, except for ">= 0" and "<= inf"
    for name, constraint in mdl.constraints.items():
        # Check if the constraint is not >= 0 or <= inf
        if constraint.sense == 'L' and constraint.constant == float('inf'):
            continue  # Ignore <= inf
        if constraint.sense == 'G' and constraint.constant == 0:
            continue  # Ignore >= 0

        print(f"   {constraint}")

    # Objective function
    print(f"Objective: {mdl.objective}")
    print(f" {mdl.sense}")

    print("--------------------")


# Solve the model
def solve_model(mdl, production_vars, products):
    status = mdl.solve()

    if status != 1:  # 1 indica solución óptima en PuLP
        print("Model cannot be solved.")
        sys.exit(1)

    obj = mdl.objective.value()

    print(f"* Production model solved with objective: {obj}")
    print(f"* Total benefit={obj}")
    for p in products:
        prod_var = production_vars[p[0]]
        print(f"Production of {p[0]}: {prod_var.varValue}")

