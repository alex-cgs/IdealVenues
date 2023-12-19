from gurobipy import *

class Venue:
    def __init__(self, name, theta, delta, crowd_size):
        self.name = name
        self.theta = theta
        self.delta = delta
        self.crowd_size = crowd_size

class Painting:
    def __init__(self, name, theta, delta, popularity):
        self.name = name
        self.theta = theta
        self.delta = delta
        self.popularity = popularity

class PathRecommendationModel:
    def __init__(self, venues, paintings, consecutive_venues, lambda_val, T_ava, Tt_ava, Cr_t):
        self.model = Model()
        self.venues = venues
        self.paintings = paintings
        self.consecutive_venues = consecutive_venues
        self.lambda_val = lambda_val
        self.T_ava = T_ava
        self.Tt_ava = Tt_ava
        self.Cr_t = Cr_t
        self.travel_distance_objective = None
        self.inv_distance = None  # Variable for the reciprocal of travel distance

    def create_variables(self, distance_matrix):
        # Decision variables for venues in the path
        v_indices = range(len(self.venues))
        v_variables = self.model.addVars(v_indices, vtype=GRB.BINARY, name="v_variables")
        
        # Decision variables for paintings
        p_indices = range(len(self.paintings))
        p_variables = self.model.addVars(p_indices, vtype=GRB.BINARY, name="p_variables")
        
        # Decision variable for the inverse of travel distance
        self.inv_distance = self.model.addVar(vtype=GRB.CONTINUOUS, name="inv_distance")
        
        print(self.venues)
        
        # Create the travel distance objective
        self.travel_distance_objective = quicksum(
            distance_matrix[(self.venues[i].name, self.venues[j].name)] * v_variables[i] * v_variables[j]
            for i, j in itertools.combinations(range(len(self.venues)), 2)
        )
        
        return v_variables, p_variables


    def set_objective(self, v_variables, p_variables):
        # Objective function for quality - Policy 1
        quality_objective = quicksum(self.venues[i].theta * v_variables[i] for i in range(len(self.venues)))
        
        # Objective function for quantity - Policy 1
        quantity_objective = quicksum(self.venues[i].delta * v_variables[i] for i in range(len(self.venues)))
        
        # Objective function for minimizing travel distance - Policy 2
        # Use the previously created travel_distance_objective
        travel_distance_objective = self.travel_distance_objective
        
        # Objective function for paintings
        painting_objective = quicksum(self.paintings[i].theta * p_variables[i] for i in range(len(self.paintings)))
        
        # Combine objectives with a trade-off parameter lambda
        combined_objective = (
            (1 - self.lambda_val) * (quality_objective + painting_objective)
            + self.lambda_val * self.inv_distance
        )
        self.model.setObjective(combined_objective, GRB.MAXIMIZE)

    def add_constraints(self, v_variables, p_variables):
        # Constraints
        print(self.consecutive_venues)
        print(v_variables.keys())
        self.model.addConstr(quicksum(p.theta * p_variables[i] for i, p in enumerate(self.paintings)) <= self.T_ava, "time_constraint")
        self.model.addConstr(quicksum(
            distance_matrix[(i, j)] * v_variables[namesIdx[i]] * v_variables[namesIdx[j]]
            for i, j in self.consecutive_venues
        ) <= self.Tt_ava, "travel_time_constraint")
        self.model.addConstr(quicksum(v.crowd_size * v_variables[i] for i, v in enumerate(self.venues)) <= self.Cr_t, "crowd_constraint")
        
        self.model.addConstr(
            self.inv_distance == 2 * self.travel_distance_objective, # Normally self.inv_distance * self.travel_distance_objective == 1
            "inv_distance_constraint"
        )


    def optimize(self):
        # Solve the optimization problem
        self.model.optimize()

# Example data (venues and paintings)
venue_Alice = Venue("Alice", theta=0.8, delta=0.5, crowd_size=30) # Venue of Alices
venue_Bob = Venue("Bob", theta=0.6, delta=0.4, crowd_size=40)
venue_Charlie = Venue("Charlie", theta=0.7, delta=0.6, crowd_size=25)
venue_Dave = Venue("Dave", theta=0.9, delta=0.3, crowd_size=35)

painting_Medieval = Painting("Medieval", theta=0.7, delta=0.4, popularity=0.8)
painting_Modern = Painting("Modern", theta=0.8, delta=0.6, popularity=0.7)
painting_Abstract = Painting("Abstract", theta=0.6, delta=0.5, popularity=0.9)
painting_Impressionist = Painting("Impressionist", theta=0.9, delta=0.7, popularity=0.6)

venues = [venue_Alice, venue_Bob, venue_Charlie, venue_Dave]
paintings = [painting_Medieval, painting_Modern, painting_Abstract, painting_Impressionist]

consecutive_venues = [(venue_Alice.name, venue_Bob.name), (venue_Bob.name, venue_Charlie.name), (venue_Charlie.name, venue_Dave.name)]

lambda_val = 0.5
T_ava = 60
Tt_ava = 20
Cr_t = 100

# Distance matrix (replace this with your actual distance matrix)
distance_matrix = {
    (venue_Alice.name, venue_Bob.name): 10,
    (venue_Alice.name, venue_Charlie.name): 10,
    (venue_Alice.name, venue_Dave.name): 20,
    (venue_Bob.name, venue_Charlie.name): 15,
    (venue_Bob.name, venue_Dave.name): 5,
    (venue_Charlie.name, venue_Dave.name): 12
}

namesIdx = {
    'Alice': 0,
    'Bob': 1,
    'Charlie': 2,
    'Dave': 3
}

# Create and solve the recommendation model
path_model = PathRecommendationModel(venues, paintings, consecutive_venues, lambda_val, T_ava, Tt_ava, Cr_t)
v_variables, p_variables = path_model.create_variables(distance_matrix)
path_model.set_objective(v_variables, p_variables)
path_model.add_constraints(v_variables, p_variables)
path_model.optimize()

# Extract the solution for the optimal path and paintings
optimal_path = {v.name: v_variables[i].x for i, v in enumerate(venues)}
optimal_paintings = {p.name: p_variables[i].x for i, p in enumerate(paintings)}

# Print the solution for the optimal path and paintings
print("Optimal Path:", optimal_path)
print("Optimal Paintings:", optimal_paintings)