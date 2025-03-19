from fastapi import APIRouter, HTTPException, Depends
from backend.database import get_db
from backend.models.user import User
from pydantic import BaseModel
import heapq

router = APIRouter()

# ✅ Define the Pydantic model for request validation
class UserCreate(BaseModel):
    name: str
    age: int
    gender: str
    hobbies: list[str]

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
def add_friend(user1: str, user2: str):
    """Connects two users as friends."""
    db = get_db()
    query = """
    MATCH (u1:User {name: $user1}), (u2:User {name: $user2})
    MERGE (u1)-[:FRIENDS_WITH]->(u2)
    MERGE (u2)-[:FRIENDS_WITH]->(u1)
    """
    db.run_query(query, {"user1": user1, "user2": user2})
    return {"message": f"{user1} and {user2} are now friends"}

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

@router.get("/recommendations/{username}")
def get_recommendations(username: str):
    """Finds friend recommendations using BFS and ranks them by similarity score."""
    db = get_db()

    # Fetch user details
    user_query = """
    MATCH (u:User {name: $username}) 
    RETURN u.age AS age, u.hobbies AS hobbies
    """
    user_data = db.run_query(user_query, {"username": username}).single()

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    user = User(username, user_data["age"], user_data["hobbies"])

    # Find friends-of-friends (FoF)
    fof_query = """
    MATCH (u:User {name: $username})-[:FRIENDS_WITH]->(friend)-[:FRIENDS_WITH]->(fof)
    WHERE NOT (u)-[:FRIENDS_WITH]->(fof) AND u <> fof
    RETURN DISTINCT fof.name AS name, fof.age AS age, fof.hobbies AS hobbies
    """
    result = db.run_query(fof_query, {"username": username})

    if not result:
        return {"recommendations": []}

    # Declare max heap (Python’s heapq is a min-heap by default, so we use a list and sort)
    max_heap = []
    
    for record in result:
        potential_friend = {
            "name": record["name"],
            "age": record["age"],
            "hobbies": record["hobbies"],
        }
        similarity_score = calculate_similarity(user, potential_friend)
        max_heap.append((similarity_score, potential_friend["name"]))  # Normal max heap

    # Sort in descending order for max heap behavior
    max_heap.sort(reverse=True, key=lambda x: x[0])

    # Extract top recommendations
    recommendations = [{"name": name, "score": score} for score, name in max_heap]

    return {"recommendations": recommendations}
