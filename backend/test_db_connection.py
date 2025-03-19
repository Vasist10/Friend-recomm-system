from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
username = "neo4j"
password = "Vasist@10"  # Change this to your Neo4j password

def test_connection():
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 'Neo4j is connected' AS message")
            for record in result:
                print(record["message"])
        driver.close()
    except Exception as e:
        print("Error:", e)

test_connection()
