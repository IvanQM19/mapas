from flask import Flask, request, render_template
import googlemaps
from datetime import datetime, timedelta
import heapq

app = Flask(__name__)

# Reemplaza 'TU_API_KEY' con tu clave API de Google Maps
API_KEY = 'AIzaSyCp-9uuzH1C7BVWpq09YDfrd89K_cGjL1Q'
gmaps = googlemaps.Client(key=API_KEY)

def obtener_ruta(origen, destino, paradas):
    ahora = datetime.now()
    ruta = gmaps.directions(origen,
                            destino,
                            waypoints=paradas,
                            mode="driving",
                            departure_time=ahora,
                            traffic_model="best_guess")
    return ruta

def calcular_consumo_combustible(distancia_km, eficiencia_km_por_l):
    return distancia_km / eficiencia_km_por_l

def convertir_duracion(duracion_segundos):
    horas = duracion_segundos // 3600
    minutos = (duracion_segundos % 3600) // 60
    return f"{int(horas)} horas y {int(minutos)} minutos"

def dijkstra(graph, start, end):
    queue = [(0, start, [])]
    seen = set()
    min_dist = {start: 0}
    
    while queue:
        (cost, v1, path) = heapq.heappop(queue)
        
        if v1 in seen:
            continue
        
        path = path + [v1]
        seen.add(v1)
        
        if v1 == end:
            return (cost, path)
        
        for v2, c in graph.get(v1, {}).items():
            if v2 in seen:
                continue
            
            prev = min_dist.get(v2, None)
            next = cost + c
            if prev is None or next < prev:
                min_dist[v2] = next
                heapq.heappush(queue, (next, v2, path))
    
    return float("inf"), []

def tsp(graph, start):
    n = len(graph)
    all_visited = (1 << n) - 1
    
    memo = {}
    
    def visit(city, visited):
        if visited == all_visited:
            return graph[city][start]
        
        if (city, visited) in memo:
            return memo[(city, visited)]
        
        cost = float("inf")
        for next_city in range(n):
            if visited & (1 << next_city) == 0:
                cost = min(cost, graph[city][next_city] + visit(next_city, visited | (1 << next_city)))
        
        memo[(city, visited)] = cost
        return cost
    
    return visit(start, 1 << start)

def crear_grafo(paradas):
    n = len(paradas)
    graph = {i: {} for i in range(n)}
    
    for i in range(n):
        for j in range(i + 1, n):
            distancia = gmaps.distance_matrix(paradas[i], paradas[j])['rows'][0]['elements'][0]['distance']['value'] / 1000
            graph[i][j] = distancia
            graph[j][i] = distancia
    
    return graph

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ruta', methods=['POST'])
def mostrar_ruta():
    origen = request.form['origen']
    destino = request.form['destino']
    paradas = [p.strip() for p in request.form['paradas'].split(',')]
    eficiencia_km_por_l = float(request.form['eficiencia'])
    algoritmo = request.form['algoritmo']
    
    if algoritmo == 'ninguno':
        ruta_gmaps = obtener_ruta(origen, destino, paradas)
        paradas_optimizadas = paradas
    else:
        # Crear lista completa de paradas incluyendo origen y destino
        todas_paradas = [origen] + paradas + [destino]
        
        # Crear grafo para Dijkstra y TSP
        grafo = crear_grafo(todas_paradas)
        
        if algoritmo == 'dijkstra':
            _, ruta_optima = dijkstra(grafo, 0, len(todas_paradas) - 1)
        else:
            costo_optimo = tsp(grafo, 0)
            ruta_optima = list(range(len(todas_paradas)))
        
        paradas_optimizadas = [todas_paradas[i] for i in ruta_optima[1:-1]]
        ruta_gmaps = obtener_ruta(origen, destino, paradas_optimizadas)
    
    distancia_total_gmaps = sum(leg['distance']['value'] for leg in ruta_gmaps[0]['legs']) / 1000
    consumo_combustible_gmaps = calcular_consumo_combustible(distancia_total_gmaps, eficiencia_km_por_l)
    
    duracion_total_segundos = sum(leg['duration']['value'] for leg in ruta_gmaps[0]['legs'])
    duracion_total = convertir_duracion(duracion_total_segundos)
    
    llegada_estimada = datetime.now() + timedelta(seconds=sum(leg.get('duration_in_traffic', leg['duration'])['value'] for leg in ruta_gmaps[0]['legs']))
    
    return render_template('ruta.html', 
                           ruta_gmaps=ruta_gmaps,
                           consumo_combustible_gmaps=consumo_combustible_gmaps,
                           distancia_total_gmaps=distancia_total_gmaps,
                           duracion_total=duracion_total,
                           llegada_estimada=llegada_estimada.strftime("%Y-%m-%d %H:%M:%S"),
                           waypoints=paradas_optimizadas,
                           algoritmo=algoritmo)

if __name__ == '__main__':
    app.run(debug=True)













