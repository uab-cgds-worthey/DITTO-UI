import os
from langchain.llms import HuggingFaceHub
from langchain.agents.agent_types import AgentType
from langchain.chains import LLMChain
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.prompts import PromptTemplate
import pandas as pd

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"

question = "Who won the FIFA World Cup in the year 1994? "

template = """Question: {question}

Answer: Let's think step by step."""

prompt = PromptTemplate(template=template, input_variables=["question"])

repo_id = "mistralai/Mistral-7B-Instruct-v0.1"  # See https://huggingface.co/models?pipeline_tag=text-generation&sort=downloads for some other options

llm = HuggingFaceHub(
    repo_id=repo_id, model_kwargs={"temperature": 0.5}#, "max_length": 200}
)

# Test on some sample data
df = pd.DataFrame(
    {
        "city": ["Toronto", "Tokyo", "Berlin"],
        "population": [2930000, 13960000, 3645000],
    }
)

# llm_chain = LLMChain(prompt=prompt, llm=llm)

# print(llm_chain.run(question))

agent = create_pandas_dataframe_agent(llm, df, verbose=True,agent_type=AgentType.OPENAI_FUNCTIONS)
query = "how many columns are there?"
query = query + " using tool python_repl_ast"
agent.run(query)
