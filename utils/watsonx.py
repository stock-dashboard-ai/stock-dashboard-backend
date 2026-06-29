import os
from langchain_ibm import ChatWatsonx, WatsonxEmbeddings
from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames
from pydantic import SecretStr

LLAMA4 = "meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
LLAMA3 = "meta-llama/llama-3-3-70b-instruct"
EMBED_MODEL = "ibm/granite-embedding-278m-multilingual"


def get_llm(model_id: str = LLAMA4) -> ChatWatsonx:
    return ChatWatsonx(
        model_id=model_id,
        url=SecretStr(os.environ["WATSONX_URL"]),
        api_key=SecretStr(os.environ["WATSONX_API_KEY"]),
        project_id=os.environ["WATSONX_PROJECT_ID"],
        params={
            "temperature": 0,
            "max_tokens": 1024,
            "frequency_penalty": 0.1,
        },
    )


def get_embedder() -> WatsonxEmbeddings:
    return WatsonxEmbeddings(
        model_id=EMBED_MODEL,
        url=SecretStr(os.environ["WATSONX_URL"]),
        api_key=SecretStr(os.environ["WATSONX_API_KEY"]),
        project_id=os.environ["WATSONX_PROJECT_ID"],
        params={EmbedTextParamsMetaNames.TRUNCATE_INPUT_TOKENS: 512},
    )
