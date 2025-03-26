import os
import logging
from typing import List, Dict, Any, Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import neo4j
from dotenv import load_dotenv

class Dota2DeepSeekRAG:
    """
    Retrieval-Augmented Generation System for Dota 2 Analysis
    
    Architectural Design Principles:
    - Open-source NLP capabilities
    - Graph-based knowledge retrieval
    - Modular, extensible design
    """
    
    def __init__(
        self, 
        neo4j_uri: str, 
        neo4j_user: str, 
        neo4j_password: str,
        model_name: str = "deepseek-ai/deepseek-coder-6.7b-instruct"
    ):
        """
        Initialize RAG system with Neo4j and DeepSeek
        
        Args:
            neo4j_uri (str): Neo4j database connection URI
            neo4j_user (str): Neo4j username
            neo4j_password (str): Neo4j password
            model_name (str): DeepSeek model identifier
        """
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Neo4j Connection
        self.neo4j_driver = neo4j.GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password)
        )
        
        # DeepSeek Model Initialization
        self.logger.info(f"Loading DeepSeek model: {model_name}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                torch_dtype=torch.float16,
                device_map='auto'
            )
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
            raise
        
        # Configuration parameters
        self.max_context_length = 4096
        self.generation_config = {
            'max_new_tokens': 512,
            'temperature': 0.7,
            'top_p': 0.9,
            'do_sample': True
        }

    def _generate_cypher_query(self, natural_language_query: str) -> str:
        """
        Generate Cypher query using DeepSeek's language understanding
        
        Args:
            natural_language_query (str): User's input query
        
        Returns:
            Cypher query for graph database retrieval
        """
        # Prompt engineering for query translation
        prompt = f"""
        You are an expert in translating natural language questions about Dota 2 
        into Neo4j Cypher graph queries. Convert the following query:

        Natural Language Query: {natural_language_query}

        Constraints:
        - Focus on retrieving meaningful Dota 2 insights
        - Use graph relationships intelligently
        - Prioritize relevant, concise data retrieval

        Example Mappings:
        - "Best hero builds" → MATCH (h:Hero)-[:HAS_META_SNAPSHOT]->(ms:MetaSnapshot)
        - "Win rate changes" → MATCH (h:Hero)-[:HAS_META_SNAPSHOT]->(ms:MetaSnapshot)

        Generate the most appropriate Cypher query:
        """
        
        # Tokenize and generate
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        try:
            outputs = self.model.generate(
                **inputs, 
                **self.generation_config
            )
            
            # Decode the generated query
            cypher_query = self.tokenizer.decode(
                outputs[0], 
                skip_special_tokens=True
            ).split("Generate the most appropriate Cypher query:")[-1].strip()
            
            return cypher_query
        
        except Exception as e:
            self.logger.error(f"Cypher query generation error: {e}")
            return ""

    def retrieve_graph_data(self, natural_language_query: str) -> List[Dict[str, Any]]:
        """
        Retrieve data from Neo4j graph based on natural language query
        
        Args:
            natural_language_query (str): User's question
        
        Returns:
            List of retrieved graph data
        """
        # Generate Cypher query
        cypher_query = self._generate_cypher_query(natural_language_query)
        
        # Execute query
        with self.neo4j_driver.session() as session:
            try:
                result = session.run(cypher_query)
                return [record.data() for record in result]
            except Exception as e:
                self.logger.error(f"Graph query execution error: {e}")
                return []

    def generate_response(
        self, 
        natural_language_query: str, 
        graph_data: List[Dict[str, Any]]
    ) -> str:
        """
        Generate natural language response using DeepSeek
        
        Args:
            natural_language_query (str): Original user question
            graph_data (List[Dict]): Data retrieved from graph
        
        Returns:
            Detailed natural language explanation
        """
        # Prepare context
        context = "\n".join(str(item) for item in graph_data)
        
        # Prompt for response generation
        prompt = f"""
        Dota 2 Analysis Task:
        
        Question: {natural_language_query}
        
        Retrieved Graph Data Context:
        {context}
        
        Using the retrieved data, provide a comprehensive, 
        analytical response that:
        - Explains the key insights
        - Provides strategic implications
        - Uses clear, professional language
        - Highlights interesting patterns
        
        Response:
        """
        
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        try:
            # Generate response
            outputs = self.model.generate(
                **inputs, 
                **self.generation_config
            )
            
            # Decode response
            response = self.tokenizer.decode(
                outputs[0], 
                skip_special_tokens=True
            ).split("Response:")[-1].strip()
            
            return response
        
        except Exception as e:
            self.logger.error(f"Response generation error: {e}")
            return "I apologize, but I couldn't generate a detailed response."

    def ask_question(self, natural_language_query: str) -> str:
        """
        Primary method for asking questions about Dota 2 data
        
        Args:
            natural_language_query (str): User's question
        
        Returns:
            Detailed natural language response
        """
        # Retrieve graph data
        graph_data = self.retrieve_graph_data(natural_language_query)
        
        # Generate natural language response
        response = self.generate_response(
            natural_language_query, 
            graph_data
        )
        
        return response

    def close(self):
        """Close database connection"""
        self.neo4j_driver.close()

def main():
    """
    Demonstration of Dota 2 RAG System with DeepSeek
    """
    # Load environment variables
    load_dotenv()
    
    # Initialize RAG Assistant
    rag_assistant = Dota2DeepSeekRAG(
        neo4j_uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        neo4j_user=os.getenv('NEO4J_USER', 'neo4j'),
        neo4j_password=os.getenv('NEO4J_PASSWORD')
    )
    
    try:
        # Example Questions
        questions = [
            "What are the most successful item builds for Anti-Mage?",
            "How have hero win rates changed in recent patches?",
            "Which heroes have shown the most significant performance improvements?"
        ]
        
        # Ask each question and print response
        for question in questions:
            print(f"\n--- Question: {question} ---")
            response = rag_assistant.ask_question(question)
            print(response)
    
    except Exception as e:
        print(f"Error in RAG demonstration: {e}")
    
    finally:
        rag_assistant.close()

if __name__ == '__main__':
    main()
