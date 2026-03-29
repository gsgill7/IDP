from machine import Pin
from utime import sleep

# ------------------ GRAPH NAVIGATION ------------------

# Map[node][neighbor] = direction (0=N, 1=E, 2=S, 3=W)
maze_map = {
    "BoxInside": {"BoxEntrance": 0},
    "BoxEntrance": {"BoxJunction": 0, "BoxInside": 2},
    "BoxJunction": {"YellowJunction": 1, "BoxEntrance": 2, "GreenJunction": 3},
    "GreenJunction": {"BoxJunction": 1, "Green": 2, "BlueJunction": 3},
    "Green": {"GreenJunction": 0},
    "BlueJunction": {"LowerRackA6": 0, "GreenJunction": 1, "Blue": 2},
    "Blue": {"BlueJunction": 0},
    "YellowJunction": {"RedJunction": 1, "Yellow": 2, "BoxJunction": 3},
    "Yellow": {"YellowJunction": 0},
    "RedJunction": {"LowerRackB1": 0, "YellowJunction": 3, "Red": 2},
    "Red": {"RedJunction": 0},
    "LowerRackA6": {"LowerRackA5": 0, "BlueJunction": 2},
    "LowerRackA5": {"LowerRackA4": 0, "LowerRackA6": 2},
    "LowerRackA4": {"LowerRackA3": 0, "LowerRackA5": 2},
    "LowerRackA3": {"LowerRackA2": 0, "LowerRackA4": 2},
    "LowerRackA2": {"LowerRackA1": 0, "LowerRackA3": 2},
    "LowerRackA1": {"LeftCross": 0, "LowerRackA2": 2},
    "LeftCross": {"BackLeftTurn": 0, "LowerRackA1": 2},
    "BackLeftTurn": {"LowerRamp": 1, "LeftCross": 2},
    "LowerRackB1": {"LowerRackB2": 0, "RedJunction": 2},
    "LowerRackB2": {"LowerRackB3": 0, "LowerRackB1": 2},
    "LowerRackB3": {"LowerRackB4": 0, "LowerRackB2": 2},
    "LowerRackB4": {"LowerRackB5": 0, "LowerRackB3": 2},
    "LowerRackB5": {"LowerRampB6": 0, "LowerRackB4": 2},
    "LowerRampB6": {"RightCross": 0, "LowerRackB5": 2},
    "RightCross": {"BackRightTurn": 0, "LowerRampB6": 2},
    "BackRightTurn": {"RightCross": 2, "LowerRamp": 3},
    "LowerRamp": {"BackRightTurn": 1, "UpperRamp": 2, "BackLeftTurn": 3},
    "UpperRamp": {"LowerRamp": 0, "UpperRightTurn": 1, "UpperLeftTurn": 3},
    "UpperRightTurn": {"UpperRackB6": 0, "UpperRamp": 3},
    "UpperRackB6": {"UpperRackB5": 0, "UpperRightTurn": 2},
    "UpperRackB5": {"UpperRackB4": 0, "UpperRackB6": 2},
    "UpperRackB4": {"UpperRackB3": 0, "UpperRackB5": 2},
    "UpperRackB3": {"UpperRackB2": 0, "UpperRackB4": 2},
    "UpperRackB2": {"UpperRackB1": 0, "UpperRackB3": 2},
    "UpperRackB1": {"UpperRackB2": 2},
    "UpperLeftTurn": {"UpperRackA1": 0, "UpperRamp": 1},
    "UpperRackA1": {"UpperRackA2": 0, "UpperLeftTurn": 2},
    "UpperRackA2": {"UpperRackA3": 0, "UpperRackA1": 2},
    "UpperRackA3": {"UpperRackA4": 0, "UpperRackA2": 2},
    "UpperRackA4": {"UpperRackA5": 0, "UpperRackA3": 2},
    "UpperRackA5": {"UpperRackA6": 0, "UpperRackA4": 2},
    "UpperRackA6": {"UpperRackA5": 2}
}

def find_shortest_path(start_node, end_node):
    """
    Find the shortest path between two nodes using Dijkstra's algorithm.
    
    Args:
        start_node: Starting node name (string)
        end_node: Destination node name (string)
    
    Returns:
        List of node names representing the shortest path, or None if no path exists
    """
    if start_node not in maze_map:
        print(f"Error: Start node '{start_node}' not found in maze map")
        return None
    
    if end_node not in maze_map and end_node not in [neighbor for neighbors in maze_map.values() for neighbor in neighbors]:
        print(f"Error: End node '{end_node}' not found in maze map")
        return None
    
    # Initialize distances and previous nodes
    distances = {node: float('inf') for node in maze_map}
    distances[start_node] = 0
    # Allow previous to hold either None or a node name string for type checkers
    try:
        from typing import Dict, Optional  # type: ignore
        previous: Dict[str, Optional[str]] = {node: None for node in maze_map}
    except Exception:
        # typing may not be available in MicroPython at runtime; fall back without annotation
        previous = {node: None for node in maze_map}
    unvisited = set(maze_map.keys())
    
    # Add end_node to unvisited if it's not already in maze_map
    if end_node not in maze_map:
        distances[end_node] = float('inf')
        previous[end_node] = None
        unvisited.add(end_node)
    
    while unvisited:
        # Find unvisited node with minimum distance
        current = min(unvisited, key=lambda node: distances[node])
        
        # If we reached the destination or no path exists
        if current == end_node or distances[current] == float('inf'):
            break
        
        unvisited.remove(current)
        
        # Check all neighbors of current node
        if current in maze_map:
            for neighbor in maze_map[current]:
                if neighbor in unvisited:
                    # All edges have weight 1 (equal distance between adjacent nodes)
                    alt_distance = distances[current] + 1
                    
                    if alt_distance < distances[neighbor]:
                        distances[neighbor] = alt_distance
                        previous[neighbor] = current
    
    # Reconstruct path
    if distances[end_node] == float('inf'):
        print(f"No path found from '{start_node}' to '{end_node}'")
        return None
    
    path = []
    current = end_node
    while current is not None:
        path.insert(0, current)
        current = previous[current]
    
    print(f"Shortest path from '{start_node}' to '{end_node}': {path}")
    print(f"Path length: {len(path) - 1} steps")
    
    return path

def relative_turn(current_dir, new_dir):
    """
    Calculate the relative turn needed to go from current_dir to new_dir.
    
    Args:
        current_dir: Current direction (0=N, 1=E, 2=S, 3=W)
        new_dir: New direction (0=N, 1=E, 2=S, 3=W)
    
    Returns:
        +1 for right turn, -1 for left turn, 2 for U-turn, 0 for straight
    """
    diff = (new_dir - current_dir) % 4
    if diff == 1:  return +1   # turn right
    if diff == 3:  return -1   # turn left
    if diff == 2:  return  2   # U-turn
    return 0                   # straight

def get_direction_name(direction):
    """
    Convert direction number to human-readable name.
    
    Args:
        direction: Direction number (0=N, 1=E, 2=S, 3=W)
    
    Returns:
        String name of the direction
    """
    directions = ["North", "East", "South", "West"]
    return directions[direction] if 0 <= direction <= 3 else "Unknown"

def get_all_nodes():
    """
    Get a list of all nodes in the maze map.
    
    Returns:
        List of all node names
    """
    nodes = set(maze_map.keys())
    # Add nodes that appear as neighbors but not as keys
    for neighbors in maze_map.values():
        nodes.update(neighbors.keys())
    return sorted(list(nodes))

def get_node_connections(node):
    """
    Get all connections from a specific node.
    
    Args:
        node: Node name (string)
    
    Returns:
        Dictionary of {neighbor: direction} or None if node doesn't exist
    """
    if node in maze_map:
        return maze_map[node].copy()
    else:
        print(f"Node '{node}' not found in maze map")
        return None
