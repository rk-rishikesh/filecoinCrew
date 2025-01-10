from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
import requests
from lighthouseweb3 import Lighthouse
from pydantic import BaseModel, Field

class DataHash(BaseModel):
	"""Data model"""
	cid: str = Field(..., description="CID of the report")
	
@tool("Filecoin JSON data Reader tool")
def filecoin_json_reader(url: str) -> str:
	"""Filecoin JSON Reader tool receives a URL input and returns the JSON data from the URL."""
	# Tool logic here
	try:
		response = requests.get(url)
		response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
		json_data = response.json()  # Parse the response content as JSON
		return json_data
	except requests.exceptions.RequestException as e:
		print(f"Error fetching data from URL: {e}")
		return None
	except ValueError as e:
		print(f"Error parsing JSON data: {e}")
		return None
	
@tool("Lighthouse Storage Tool")
def lighthouse_storage_tool() -> str:
	"""A tool to store data on Filecoin via Lighthouse"""
	# Tool logic here
	lh = Lighthouse(token="LIGHTHOUSE_TOKEN")
	response = lh.upload("lighthousereport.md")
	hash_value = response.get('data', {}).get('Hash')
	return hash_value

# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Filecoincrew():
	"""Filecoincrew crew"""
	# Learn more about YAML configuration files here:
	# Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
	# Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
	@agent
	def researcher(self) -> Agent:
		return Agent(
			config=self.agents_config['researcher'],
			tools=[filecoin_json_reader],
			verbose=True
		)

	@agent
	def reporting_analyst(self) -> Agent:
		return Agent(
			config=self.agents_config['reporting_analyst'],
			verbose=True
		)

	@agent
	def database_engineer(self) -> Agent:
		return Agent(
			config=self.agents_config['database_engineer'],
			tools=[lighthouse_storage_tool],
			verbose=True
		)
	
	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def research_task(self) -> Task:
		return Task(
			config=self.tasks_config['research_task'],
		)

	@task
	def reporting_task(self) -> Task:
		return Task(
			config=self.tasks_config['reporting_task'],
			output_file='lighthousereport.md'
		)

	@task
	def storage_task(self) -> Task:
		return Task(
			config=self.tasks_config['storage_task'],
			output_json=DataHash
		)
	
	@crew
	def crew(self) -> Crew:
		"""Creates the Filecoincrew crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
