### Description: This file contains the functions to interact with the Neo4j graph database.
### Since Neo4j does not have a free tier, we had to use a different database for our project.
### The code below is left as an example of how we would have implemented the graph database.

from neo4j import GraphDatabase, basic_auth
from neomodel import RelationshipTo, StringProperty, StructuredNode

from config import CONFIG

driver = GraphDatabase.driver(f'bolt://{CONFIG.neo4j_uri}',
                              auth=basic_auth(CONFIG.neo4j_username,
                                              CONFIG.neo4j_password))


class UserNode(StructuredNode):
    username = StringProperty()
    uuid = StringProperty(unique_index=True)
    avatar = StringProperty()
    following = RelationshipTo("UserNode", "FOLLOWS")


def get_followers(username: str):

    with driver.session() as session:
        result = session.execute_read(
            lambda tx: tx.run("""
            MATCH (user:UserNode {username: $username})<-[:FOLLOWS]-(follower:UserNode)
            RETURN follower.username as username, follower.avatar as avatar, follower.uuid as uuid
            """,
                              username=username).data())
        return [dict(record) for record in result]


def get_following(username: str):

    with driver.session() as session:
        result = session.execute_read(
            lambda tx: tx.run("""
              MATCH (user:UserNode {username: $username})-[:FOLLOWS]->(following:UserNode)
              RETURN following.username as username, following.avatar as avatar, following.uuid as uuid
              """,
                              username=username).data())
        return [dict(record) for record in result]


def get_mutual_frields(username: str, other_username: str):

    with driver.session() as session:
        result = session.execute_read(
            lambda tx: tx.run("""
            MATCH (user:UserNode {username: $username})-[:FOLLOWS]->(mutual:UserNode)<-[:FOLLOWS]-(other:UserNode {username: $other_username})
            RETURN mutual.username as username, mutual.avatar as avatar, mutual.uuid as uuid
            """,
                              username=username,
                              other_username=other_username).data())
        return [dict(record) for record in result]
