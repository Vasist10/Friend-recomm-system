from neo4j import GraphDatabase

# Connection details
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "Vasist@10"  # Change if you updated it

class Database:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        self._initialize_you_node()  # Uncommented this line

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            return session.run(query, parameters)

    def _initialize_you_node(self):
        """Creates the initial 'You' node if it doesn't exist"""
        query = """
        MERGE (u:User {name: 'You'})
        ON CREATE SET
            u.age = 25,
            u.gender = 'Unknown',
            u.hobbies = ['reading', 'music']
        RETURN u
        """
        try:
            with self.driver.session() as session:
                result = session.run(query)
                print("✅ Initial 'You' node created/verified in Neo4j")
        except Exception as e:
            print(f"❌ Failed to initialize 'You' node: {str(e)}")

# Create an instance
db = Database()

def get_db():
    return db