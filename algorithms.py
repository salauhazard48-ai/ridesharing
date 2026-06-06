import heapq
import networkx as nx

# ── Route Graph ────────────────────────────────────────────────────────────
GRAPH_DATA = {
    'Lagos':         {'Abuja': 760,  'Ibadan': 130, 'Kano': 1050, 'Enugu': 530, 'Port Harcourt': 660},
    'Ibadan':        {'Lagos': 130,  'Abuja': 640},
    'Abuja':         {'Lagos': 760,  'Kano': 310,   'Ibadan': 640},
    'Kano':          {'Abuja': 310,  'Lagos': 1050},
    'Enugu':         {'Lagos': 530},
    'Port Harcourt': {'Lagos': 660}
}

CITIES = list(GRAPH_DATA.keys())

# ── Build NetworkX Graph ───────────────────────────────────────────────────
def build_graph():
    G = nx.DiGraph()
    for origin, neighbours in GRAPH_DATA.items():
        for destination, distance in neighbours.items():
            G.add_edge(origin, destination, weight=distance)
    return G

# Create the graph once at module load
G = build_graph()


# ── Algorithm 1: Dijkstra Shortest Path (using NetworkX) ──────────────────
def dijkstra(origin, destination):
    try:
        # NetworkX shortest_path uses Dijkstra's algorithm when weight is specified
        path = nx.shortest_path(G, source=origin, target=destination, weight='weight')
        distance = nx.shortest_path_length(G, source=origin, target=destination, weight='weight')
        return path, distance
    except nx.NetworkXNoPath:
        return None, None
    except nx.NodeNotFound:
        return None, None


# ── Algorithm 2: Five-Stage Passenger Matching ────────────────────────────
def match_trips(passenger_origin, passenger_destination, preferred_time,
                seats_needed, max_budget, available_trips, route_distance):

    TIME_WINDOW = 120
    RATE_PER_KM = 14.8
    OVERHEAD    = 0.15
    matched     = []

    def time_to_mins(t):
        h, m = map(int, t.split(':'))
        return h * 60 + m

    passenger_mins = time_to_mins(preferred_time)

    for trip in available_trips:
        # Stage 1 — origin and destination match
        if trip['origin'] != passenger_origin:
            continue
        if trip['destination'] != passenger_destination:
            continue

        # Stage 2 — time window check
        trip_mins = time_to_mins(trip['departure_time'])
        time_diff = abs(trip_mins - passenger_mins)
        if time_diff > TIME_WINDOW:
            continue

        # Stage 3 — seat availability
        if trip['available_seats'] < seats_needed:
            continue

        # Stage 4 — budget check
        total_passengers = (trip['total_seats'] - trip['available_seats']) + seats_needed
        fare = round((route_distance * RATE_PER_KM * (1 + OVERHEAD)) / total_passengers)
        if fare > max_budget:
            continue

        # Stage 5 — composite scoring
        time_score = round(1 - (time_diff / TIME_WINDOW), 4)
        cost_score = round(min(1, (max_budget - fare) / max_budget), 4)
        seat_score = round(trip['available_seats'] / trip['total_seats'], 4)
        fit_score  = round((0.40 * time_score) + (0.35 * cost_score) + (0.25 * seat_score), 4)

        matched.append({
            'trip':      trip,
            'fare':      fare,
            'time_diff': time_diff,
            'fit_score': fit_score
        })

    matched.sort(key=lambda x: x['fit_score'], reverse=True)
    return matched


# ── Algorithm 3: Cost Sharing ─────────────────────────────────────────────
def compute_fare(distance_km, total_passengers):
    RATE_PER_KM = 14.8
    OVERHEAD    = 0.15
    if total_passengers < 1:
        total_passengers = 1
    return round((distance_km * RATE_PER_KM * (1 + OVERHEAD)) / total_passengers)