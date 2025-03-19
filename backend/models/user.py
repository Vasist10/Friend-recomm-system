import backend.database

# Get the database instance
db = backend.database.get_db()

class User:
    @staticmethod
    def create_user(name, age, gender, hobbies):
        """Add a new user to the database."""
        query = """
        CREATE (u:User {name: $name, age: $age, gender: $gender, hobbies: $hobbies})
        RETURN u
        """
        return db.run_query(query, {"name": name, "age": age, "gender": gender, "hobbies": hobbies})

    @staticmethod
    def get_all_users():
        """Retrieve all users from the database."""
        query = "MATCH (u:User) RETURN u.name AS name, u.age AS age, u.gender AS gender, u.hobbies AS hobbies"
        result = db.run_query(query)
        return [record.data() for record in result]

    @staticmethod
    def add_friend(user1, user2):
        """Create a friendship connection between two users."""
        query = """
        MATCH (u1:User {name: $user1}), (u2:User {name: $user2})
        MERGE (u1)-[:FRIENDS_WITH]->(u2)
        MERGE (u2)-[:FRIENDS_WITH]->(u1)
        RETURN u1, u2
        """
        return db.run_query(query, {"user1": user1, "user2": user2})

    @staticmethod
    def get_friends(user):
        """Get friends of a specific user."""
        query = """
        MATCH (u:User {name: $user})-[:FRIENDS_WITH]->(friend)
        RETURN friend.name AS name, friend.age AS age, friend.gender AS gender, friend.hobbies AS hobbies
        """
        result = db.run_query(query, {"user": user})
        return [record.data() for record in result]
