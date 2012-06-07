#!/usr/bin/python2.7
''' Ant Colony Simulation '''
import random

GLOBAL_UPDATE = 10000 # 100 / length
LOCAL_UPDATE = 10 # constant
DECAY = 5
STEPS = 100
ANTS = 40
NUM_CITIES = 48

global_vertex_number = 1
class Vertex(object):
    def __init__(self,name=None):
        if name is None:
            global global_vertex_number
            self.name = global_vertex_number
            global_vertex_number += 1
        else:
            self.name = name
        self.edges = []

    def connect(self,other,weight):
        e = Edge(self,other,weight)
        self.edges.append(e)
        other.edges.append(e)

    def __repr__(self):
        return 'Vertex({0})'.format(repr(self.name))

class Edge(object):
    def __init__(self,v1,v2,weight):
        self.v1 = v1
        self.v2 = v2
        self.weight = weight
        self.pheromone = 0.0

    def __len__(self): return weight

    def drop(self,amount=LOCAL_UPDATE):
        self.pheromone += amount

    def decay(self, amount=DECAY):
        self.pheromone -= amount
        if self.pheromone < 0: self.pheromone = 0

    def __repr__(self):
        return 'Edge({0},{1},{2})'.format(repr(self.v1),repr(self.v2),repr(self.weight))

class Cycle(object):
    def __init__(self,edgelist=None):
        self.edgelist = edgelist or []

    def __len__(self): return self.weight 

    def add(self,edge): self.edgelist.append(edge)

    @property
    def weight(self): return sum([e.weight for e in self.edgelist])

    def drop(self,amount=None):
        if amount is None:
            amount = GLOBAL_UPDATE / self.weight
        for e in self.edgelist:
            e.drop(amount)

    def decay(self,amount=DECAY):
        for e in self.edgelist:
            e.decay(amount)

    def __repr__(self):
        return 'Cycle with {0} edges and w = {1}'.format(len(self.edgelist),self.weight)

class Ant(object):
    def __init__(self,num,pos):
        self.starting = pos
        self.position = pos
        self.number = num
        self.cycle = Cycle()
        self.last_edge = None
        self.visited = set()
        self.visited.add(self.starting)
        self.done = False

    def __repr__(self):
        return 'Ant({0},{1})'.format(repr(self.num),repr(self.pos))

    def __pick_edge(self, edges):
        ''' Pick the edge to follow. '''
        # Sort by pheromone
        #edges.sort(key=lambda x: -x.pheromone)
        
        # Shuffle
        random.shuffle(edges)

        # Add up total pheromone visibility
        max_pher = sum([e.pheromone for e in edges]) or 1

        # Scale edges according to their proportion of total pheromones
        edges = [(e.pheromone/max_pher,e) for e in edges]

        # Pick an edge with probability == scaled_pheromone + 0.05
        for pher,e in edges:
            if random.random() < pher + 0.05:
                break

        return e

    def __get_next(self,edge):
        if edge.v1 == self.position: return edge.v2
        return edge.v1

    def walk(self):
        ''' Pick an edge and update state to follow it. '''
        if self.done: return True

        # Copy the edge list
        edges = self.position.edges[:]

        # Remove edges leading to already-visited cities
        for edge in edges[:]:
            p = self.__get_next(edge)
            #print p, self.visited, p in self.visited
            if self.__get_next(edge) in self.visited: edges.remove(edge)
        assert len(edges) != 0

        # Pick the next edge
        e = self.__pick_edge(edges)

        #print "Ant {0} has visited {1} cities.".format(self.number,len(self.visited))
        #print "Ant {2} walking from {0} to {1}".format(self.position,self.__get_next(e),self.number)
        #print "Has visited {0}".format(self.visited)
        #print

        # Walk along edge
        e.drop() # Deposit some pheromone
        self.last_edge = e
        self.position = self.__get_next(e)
        self.cycle.add(e)

        # Append to visited
        self.visited.add(self.position)
        
        # If we've visited all the cities, we're done
        if len(self.visited) == NUM_CITIES:
            self.done = True
            return True
        else: return False

def create_cities(path):
    grid = []
    with open(path) as inp:
        for line in inp:
            line_arr = []
            for part in line.strip('\n').split(','):
                try:
                    line_arr.append( float(part) )
                except ValueError:
                    line_arr.append( part )
            grid.append(line_arr)

    cities = {}
    city_names = grid[0][1:]
    for i,city in enumerate(city_names):
        cities[city] = (Vertex(city), zip(city_names, grid[i+1][1:]))
    
    for city,listd in cities.values():
        for othername,distance in listd:
            if distance != 0.0:
                city.connect( cities[othername][0], distance )

    return [v[0] for v in cities.values()]

if __name__ == '__main__':
    cities = create_cities('/home/eswanson/cities.csv')
#    for city in cities:
#        print city
#        print city.edges
#        print

    for i in xrange(STEPS):
        ants = [Ant(a,cities[0]) for a in xrange(ANTS)]
        done = 0
        
        # While some ants haven't cycled yet
        while done < len(ants):
            for a in ants:
                # If the ant is done, this is a NOP
                if a.walk():
                    done += 1

            # Decay pheromones
            for c in cities:
                for e in c.edges:
                    e.decay()

        # Now do a global pheromone update  
        for a in ants:
            a.cycle.drop()

        # Find the shortest cycle and reinforce
        shortest = sorted([a.cycle for a in ants],key=lambda x: x.weight)[0]
        print shortest
        shortest.drop()
        print "Step {0} / {1}: shortest cycle {2}, pheromone sum {3}".format(i+1,STEPS,shortest.weight,sum([e.pheromone for e in shortest.edgelist]))
        
