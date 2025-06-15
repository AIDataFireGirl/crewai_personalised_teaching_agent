import os
from typing import List, Dict
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
import chromadb
from chromadb.config import Settings

# Load environment variables
load_dotenv()

class TeachingAgent:
    def __init__(self):
        # Initialize vector store
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=os.getenv("CHROMA_DB_DIRECTORY", "./chroma_db")
        ))

    def setup_vector_store(self, documents: List[str]):
        """Initialize and populate the vector store with documents"""
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.create_documents(documents)
        
        # Create vector store
        self.vector_store = FAISS.from_documents(texts, self.embeddings)

    def create_agents(self) -> List[Agent]:
        """Create the necessary agents for the teaching crew"""
        # Subject Matter Expert Agent
        subject_expert = Agent(
            role='Subject Matter Expert',
            goal='Provide accurate and comprehensive knowledge about the subject',
            backstory="""You are an expert in your field with years of teaching experience.
            You excel at breaking down complex concepts into understandable parts.""",
            verbose=True,
            allow_delegation=False
        )

        # Learning Style Analyzer Agent
        learning_analyzer = Agent(
            role='Learning Style Analyzer',
            goal='Analyze and adapt teaching methods based on student learning style',
            backstory="""You specialize in understanding different learning styles
            and adapting teaching methods accordingly.""",
            verbose=True,
            allow_delegation=False
        )

        # Progress Tracker Agent
        progress_tracker = Agent(
            role='Progress Tracker',
            goal='Monitor and evaluate student progress',
            backstory="""You are responsible for tracking student progress
            and providing feedback for improvement.""",
            verbose=True,
            allow_delegation=False
        )

        return [subject_expert, learning_analyzer, progress_tracker]

    def create_tasks(self, agents: List[Agent], student_info: Dict) -> List[Task]:
        """Create tasks for the teaching crew"""
        tasks = [
            Task(
                description=f"""Analyze the student's learning style and preferences:
                {student_info['learning_style']}
                Create a personalized learning plan.""",
                agent=agents[1]  # Learning Style Analyzer
            ),
            Task(
                description=f"""Based on the learning plan, prepare comprehensive
                teaching materials for the topic: {student_info['topic']}""",
                agent=agents[0]  # Subject Matter Expert
            ),
            Task(
                description="""Monitor the student's progress and provide
                detailed feedback for improvement.""",
                agent=agents[2]  # Progress Tracker
            )
        ]
        return tasks

    def run_teaching_session(self, student_info: Dict):
        """Run a complete teaching session"""
        # Setup vector store with relevant documents
        if student_info.get('documents'):
            self.setup_vector_store(student_info['documents'])

        # Create agents and tasks
        agents = self.create_agents()
        tasks = self.create_tasks(agents, student_info)

        # Create and run the crew
        crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=2,
            process=Process.sequential
        )

        result = crew.kickoff()
        return result

def main():
    # Get user input
    print("Welcome to the Personalized Teaching Agent!")
    student_info = {
        'name': input("Enter student name: "),
        'topic': input("Enter the topic to learn: "),
        'learning_style': input("Describe your learning style (visual/auditory/reading/writing): "),
        'prior_knowledge': input("Describe your prior knowledge on the topic: "),
        'goals': input("What are your learning goals? ")
    }

    # Initialize and run the teaching agent
    agent = TeachingAgent()
    result = agent.run_teaching_session(student_info)
    print("\nTeaching Session Results:")
    print(result)

if __name__ == "__main__":
    main() 