import asyncio
from fastapi import APIRouter, FastAPI, HTTPException, Depends
from backend.database import get_db
from backend.models.user import User
from pydantic import BaseModel
import heapq
import time
from typing import List, Dict
from neo4j import Result
from fastapi import Request
from fastapi.middleware import Middleware

router = APIRouter()
app = FastAPI()

# ✅ Define the Pydantic model for request validation
class UserCreate(BaseModel):
    name: str
    age: int
    gender: str
    hobbies: list[str]
class FriendRequest(BaseModel):
    user1: str
    user2: str

@router.post("/add_user/")
def add_user(user: UserCreate, db=Depends(get_db)):
    """Adds a new user to Neo4j."""
    result = db.run_query(
        """
        CREATE (u:User {name: $name, age: $age, gender: $gender, hobbies: $hobbies})
        RETURN u
        """,
        {
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
            "hobbies": user.hobbies
        },
    )
    return {"message": f"User {user.name} added successfully"}


def calculate_similarity(user, potential_friend):
    """Calculate similarity score based on common hobbies and age difference."""
    common_hobbies = len(set(user.hobbies) & set(potential_friend["hobbies"]))
    age_difference = abs(user.age - potential_friend["age"])
    return (common_hobbies * 5) - age_difference  # Weighted scoring



@router.post("/add_friend/")
def add_friend(request: FriendRequest, db=Depends(get_db)):  # Now expects JSON body
    """Connects two users as friends."""
    query = """
    MATCH (u1:User {name: $user1}), (u2:User {name: $user2})
    MERGE (u1)-[:FRIENDS_WITH]->(u2)
    MERGE (u2)-[:FRIENDS_WITH]->(u1)
    """
    db.run_query(query, {"user1": request.user1, "user2": request.user2})
    return {"message": f"{request.user1} and {request.user2} are now friends"}
    
@router.delete("/remove_friend/")
def remove_friend(user1: str, user2: str):
    """Removes friendship connection between two users."""
    db = get_db()
    query = """
    MATCH (u1:User {name: $user1})-[r:FRIENDS_WITH]-(u2:User {name: $user2})
    DELETE r
    """
    db.run_query(query, {"user1": user1, "user2": user2})
    return {"message": f"Friendship between {user1} and {user2} removed"}

@router.delete("/delete_user/{username}")
def delete_user(username: str):
    """Deletes a user and all their connections."""
    db = get_db()
    query = """
    MATCH (u:User {name: $username})
    DETACH DELETE u
    """
    db.run_query(query, {"username": username})
    return {"message": f"User {username} deleted successfully"}
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    if "/recommendations/" in str(request.url):
        # Add delay to prevent rapid firing
        await asyncio.sleep(0.5)
    return await call_next(request)


@router.get("/recommendations/{name}")
async def get_recommendations(name: str, db=Depends(get_db)):
    try:
        # Clean the input name
        name = name.strip()
        
        # 1. Fetch the complete graph structure with both incoming and outgoing relationships
        graph_query = """
        MATCH (u:User)
        OPTIONAL MATCH (u)-[r:FRIENDS_WITH]-(friend:User)
        RETURN u.name as name, u.hobbies as hobbies, u.age as age,
               collect(DISTINCT friend.name) as friends
        """
        
        with db.driver.session() as session:
            # Get graph data
            graph_data = list(session.run(graph_query))
            
            # Build adjacency list and user data with cleaned names
            graph = {}
            user_data = {}
            for record in graph_data:
                user_name = record["name"].strip() if record["name"] else ""  # Clean whitespace
                graph[user_name] = [friend.strip() for friend in record["friends"]]  # Clean friend names
                user_data[user_name] = {
                    "hobbies": set(record["hobbies"] or []),
                    "age": record["age"] or 0
                }

            print(f"Graph structure: {graph}")  # Debug print
            print(f"User data: {user_data}")    # Debug print

            if name not in user_data:
                print(f"User {name} not found. Available users: {list(user_data.keys())}")
                return {"recommendations": []}

            # 2. BFS Implementation
            def bfs_find_friends(start_node):
                from collections import deque
                queue = deque([(start_node, 0)])
                visited = {start_node: 0}
                recommendations = []

                while queue:
                    current, depth = queue.popleft()
                    
                    # Add to recommendations if it's a friend-of-friend or beyond
                    if depth >= 2:
                        recommendations.append((current, depth))
                    
                    # Only explore further if depth is less than 3
                    if depth < 3:
                        # Get all neighbors (both incoming and outgoing connections)
                        neighbors = graph.get(current, [])
                        for neighbor in neighbors:
                            if neighbor not in visited:
                                visited[neighbor] = depth + 1
                                queue.append((neighbor, depth + 1))
                                print(f"BFS: {current} -> {neighbor} at depth {depth + 1}")  # Debug print
                
                return recommendations

            # 3. Calculate Jaccard Similarity
            def calculate_jaccard_similarity(user1_hobbies, user2_hobbies):
                if not user1_hobbies or not user2_hobbies:
                    return 0
                intersection = len(user1_hobbies & user2_hobbies)
                union = len(user1_hobbies | user2_hobbies)
                return intersection / union if union > 0 else 0

            # 4. Get recommendations using BFS
            user_hobbies = user_data[name]["hobbies"]
            user_age = user_data[name]["age"]
            direct_friends = set(graph.get(name, []))
            
            print(f"Processing recommendations for {name}")  # Debug print
            print(f"Direct friends: {direct_friends}")       # Debug print
            
            # Get potential friends through BFS
            potential_friends = bfs_find_friends(name)
            print(f"Potential friends found: {potential_friends}")  # Debug print
            
            # Calculate scores using heap
            import heapq
            heap = []
            counter = 0
            
            for friend_name, depth in potential_friends:
                # Skip if it's the user themselves or a direct friend
                if friend_name == name or friend_name in direct_friends:
                    continue
                
                # Calculate Jaccard similarity
                friend_hobbies = user_data[friend_name]["hobbies"]
                jaccard_score = calculate_jaccard_similarity(user_hobbies, friend_hobbies)
                
                # Calculate age difference penalty
                age_diff = abs(user_age - user_data[friend_name]["age"])
                
                # Final score: Jaccard similarity (0-1) * 50 + network proximity bonus - age penalty
                final_score = (jaccard_score * 50) + (20 / depth) - (age_diff * 0.5)
                
                # Push to min heap with counter to break ties
                heapq.heappush(heap, (-final_score, counter, {
                    "name": friend_name,
                    "score": round(final_score, 2),
                    "jaccard_similarity": round(jaccard_score, 2),
                    "common_hobbies": len(user_hobbies & friend_hobbies),
                    "network_distance": depth
                }))
                counter += 1
            
            # Get top 20 recommendations from heap
            recommendations = []
            while heap and len(recommendations) < 20:
                score, _, rec = heapq.heappop(heap)
                recommendations.append(rec)
            
            print(f"Found {len(recommendations)} recommendations for {name}")
            print(f"Final recommendations: {recommendations}")  # Debug print
            return {"recommendations": recommendations}

    except Exception as e:
        print(f"🛡️ Armor-piercing error handling: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"recommendations": []}
