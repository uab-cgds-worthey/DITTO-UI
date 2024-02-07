#from langchain.llms import HuggingFaceHub
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

#os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
def query_llm(query, df):
    #repo_id = "google/flan-t5-xxl"  # See https://huggingface.co/models?pipeline_tag=text-generation&sort=downloads for some other options

    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613")

    agent = create_pandas_dataframe_agent(llm, df, verbose=True,agent_type=AgentType.OPENAI_FUNCTIONS)

    return agent.run(query)
