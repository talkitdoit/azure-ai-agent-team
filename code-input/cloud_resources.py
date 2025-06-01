from neo4j import GraphDatabase
from typing import Dict, List

class CloudResourceManager:
    def __init__(self):
        self.resources = {}  # Track cloud resources
        self.resource_limits = {}  # Track resource quotas/limits

    def provision_resource(self, resource_type, quantity):
        if resource_type in self.resources:
            self.resources[resource_type] += quantity
        else:
            self.resources[resource_type] = quantity

    def deprovision_resource(self, resource_type, quantity):
        if resource_type in self.resources:
            if self.resources[resource_type] >= quantity:
                self.resources[resource_type] -= quantity
                return True
        return False

    def set_resource_limit(self, resource_type, max_limit):
        self.resource_limits[resource_type] = max_limit

    def check_resource_limits(self):
        near_limit_resources = []
        for resource_type, quantity in self.resources.items():
            if resource_type in self.resource_limits:
                if quantity > self.resource_limits[resource_type] * 0.8:  # 80% threshold
                    near_limit_resources.append(resource_type)
        return near_limit_resources

class CloudResourceGraph:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def add_resource_relationships(self, resources: Dict[str, List[str]]):
        with self.driver.session() as session:
            session.execute_write(self._create_resources, resources)

    @staticmethod
    def _create_resources(tx, resources):
        # Create nodes and relationships
        query = """
        MERGE (c:Cloud {name: $cloud_name})
        WITH c
        UNWIND $resources as resource
        MERGE (r:Resource {name: resource.name, type: resource.type})
        MERGE (c)-[:CONTAINS]->(r)
        """
        tx.run(query, cloud_name="Azure", resources=resources)

    def close(self):
        self.driver.close() 