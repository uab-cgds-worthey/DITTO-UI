from langchain.llms import HuggingFaceHub
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

#os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
def query_llm(query, df):
    repo_id = "google/flan-t5-xxl"  # See https://huggingface.co/models?pipeline_tag=text-generation&sort=downloads for some other options

    llm = HuggingFaceHub(
        repo_id=repo_id, model_kwargs={"temperature": 0.5, "max_length": 500}
    )

    agent = create_pandas_dataframe_agent(llm, df, verbose=True,agent_type=AgentType.OPENAI_FUNCTIONS)
    #query = "how many columns are there?"
    query = query + " using tool python_repl_ast"
    return agent.run(query)
