import aiohttp
from typing import List, Union, Optional
from tenacity import retry, wait_random_exponential, stop_after_attempt, wait_fixed
from typing import Dict, Any
from dotenv import load_dotenv
import os
import asyncio
from openai import AsyncOpenAI
import async_timeout

from AgentDropout.llm.format import Message
from AgentDropout.llm.price import cost_count, cost_count_llama3, cost_count_deepseek
from AgentDropout.llm.llm import LLM
from AgentDropout.llm.llm_registry import LLMRegistry


load_dotenv()


def _normalize_openai_base_url(url: str) -> str:
    if not url:
        return url
    normalized = url.rstrip("/")
    if not normalized.endswith("/v1"):
        normalized = f"{normalized}/v1"
    return normalized


DEFAULT_BASE_URL = _normalize_openai_base_url(os.getenv("OPENAI_BASE_URL", os.getenv("MINE_BASE_URL", "")))
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY", os.getenv("MINE_API_KEYS", ""))
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
LOCAL_OPENAI_BASE_URL = os.getenv("LOCAL_OPENAI_BASE_URL", "http://localhost:6789/v1")
LOCAL_OPENAI_API_KEY = os.getenv("LOCAL_OPENAI_API_KEY", "API-KEY")


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    return asyncio.run(coro)


def _extract_completion_text(completion):
    if isinstance(completion, str):
        return completion
    if isinstance(completion, dict):
        if "choices" in completion and completion["choices"]:
            message = completion["choices"][0].get("message", {})
            return message.get("content", "")
        return completion.get("content", "")
    if hasattr(completion, "choices") and completion.choices:
        message = completion.choices[0].message
        if isinstance(message, dict):
            return message.get("content", "")
        return getattr(message, "content", "")
    return ""

# print(MINE_BASE_URL)


# @retry(wait=wait_random_exponential(max=100), stop=stop_after_attempt(3))
# async def achat(
#     model: str,
#     msg: List[Dict],):
#     request_url = MINE_BASE_URL
#     authorization_key = MINE_API_KEYS
#     headers = {
#         'Content-Type': 'application/json',
#         'authorization': authorization_key
#     }
#     data = {
#         "name": model,
#         "inputs": {
#             "stream": False,
#             "msg": repr(msg),
#         }
#     }
#     async with aiohttp.ClientSession() as session:
#         async with session.post(request_url, headers=headers ,json=data) as response:
#             response_data = await response.json()
#             if isinstance(response_data['data'],str):
#                 prompt = "".join([item['content'] for item in msg])
#                 cost_count(prompt,response_data['data'],model)
#                 return response_data['data']
#             else:
#                 raise Exception("api error")

@retry(wait=wait_random_exponential(max=100), stop=stop_after_attempt(3))
async def achat(
    model: str,
    msg: List[Dict],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
):
    if not DEFAULT_API_KEY:
        raise RuntimeError("OPENAI_API_KEY (or MINE_API_KEYS) is not configured.")
    api_kwargs = {"api_key": DEFAULT_API_KEY}
    if DEFAULT_BASE_URL:
        api_kwargs["base_url"] = DEFAULT_BASE_URL
    aclient = AsyncOpenAI(**api_kwargs)
    try:
        create_kwargs: Dict[str, Any] = {"model": model, "messages": msg}
        if max_tokens is not None:
            create_kwargs["max_tokens"] = int(max_tokens)
        if temperature is not None:
            create_kwargs["temperature"] = float(temperature)
        async with async_timeout.timeout(1000):
            completion = await aclient.chat.completions.create(**create_kwargs)
        response_message = _extract_completion_text(completion)
        
        if isinstance(response_message, str):
            if "<!doctype html>" in response_message.lower():
                raise RuntimeError("Received HTML response from LLM endpoint; verify base_url and gateway configuration.")
            prompt = "".join([item['content'] for item in msg])
            cost_count(prompt, response_message, model)
            return response_message

    except Exception as e:
        raise RuntimeError(f"Failed to complete the async chat request: {e}")

# @retry(wait=wait_random_exponential(max=100), stop=stop_after_attempt(6))
async def achat_deepseek(model: str, msg: List[Dict],):
    if not DEEPSEEK_API_KEY or not DEEPSEEK_BASE_URL:
        raise RuntimeError("DEEPSEEK_API_KEY/DEEPSEEK_BASE_URL is not configured.")
    api_kwargs = dict(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    aclient = AsyncOpenAI(**api_kwargs)
    try:
        async with async_timeout.timeout(1000):
            completion = await aclient.chat.completions.create(model=model,messages=msg)
        response_message = _extract_completion_text(completion)
        
        if isinstance(response_message, str):
            if "<!doctype html>" in response_message.lower():
                raise RuntimeError("Received HTML response from LLM endpoint; verify base_url and gateway configuration.")
            prompt = "".join([item['content'] for item in msg])
            cost_count_deepseek(prompt, response_message, model)
            return response_message

    except Exception as e:
        raise RuntimeError(f"Failed to complete the async chat request: {e}")

# @retry(wait=wait_random_exponential(max=100), stop=stop_after_attempt(3))
@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
async def achat_llama(model: str, msg: List[Dict]):
    # print(111111111111)
    api_kwargs = dict(api_key=LOCAL_OPENAI_API_KEY, base_url=LOCAL_OPENAI_BASE_URL)
    aclient = AsyncOpenAI(**api_kwargs)
    try:
        async with async_timeout.timeout(1000):
            completion = await aclient.chat.completions.create(model=model,messages=msg)
        response_message = _extract_completion_text(completion)
        
        if isinstance(response_message, str):
            if "<!doctype html>" in response_message.lower():
                raise RuntimeError("Received HTML response from LLM endpoint; verify base_url and gateway configuration.")
            prompt = "".join([item['content'] for item in msg])
            cost_count_llama3(prompt, response_message, model)
            return response_message

    except Exception as e:
        print(f"Error in achat_llama: {e}")
        # raise
    

@LLMRegistry.register('GPTChat')
class GPTChat(LLM):

    def __init__(self, model_name: str):
        self.model_name = model_name

    async def agen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
        ) -> Union[List[str], str]:

        if max_tokens is None:
            max_tokens = self.DEFAULT_MAX_TOKENS
        if temperature is None:
            temperature = self.DEFAULT_TEMPERATURE
        if num_comps is None:
            num_comps = self.DEFUALT_NUM_COMPLETIONS
        
        if isinstance(messages, str):
            messages = [Message(role="user", content=messages)]
        return await achat(
            self.model_name,
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    
    def gen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ) -> Union[List[str], str]:
        return _run_async(self.agen(messages, max_tokens, temperature, num_comps))

@LLMRegistry.register('deepseek')
class DeepseekChat(LLM):

    def __init__(self, model_name: str):
        self.model_name = model_name

    async def agen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
        ) -> Union[List[str], str]:

        if max_tokens is None:
            max_tokens = self.DEFAULT_MAX_TOKENS
        if temperature is None:
            temperature = self.DEFAULT_TEMPERATURE
        if num_comps is None:
            num_comps = self.DEFUALT_NUM_COMPLETIONS
        
        if isinstance(messages, str):
            messages = [Message(role="user", content=messages)]
        return await achat_deepseek(self.model_name,messages)
    
    def gen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ) -> Union[List[str], str]:
        return _run_async(self.agen(messages, max_tokens, temperature, num_comps))

@LLMRegistry.register('llama')
class LlamaChat(LLM):

    def __init__(self, model_name: str):
        self.model_name = model_name
        # print(11111111111111111111)
        # self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    async def agen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
        ) -> Union[List[str], str]:

        if max_tokens is None:
            max_tokens = self.DEFAULT_MAX_TOKENS
        if temperature is None:
            temperature = self.DEFAULT_TEMPERATURE
        if num_comps is None:
            num_comps = self.DEFUALT_NUM_COMPLETIONS
        
        if isinstance(messages, str):
            messages = [Message(role="user", content=messages)]
        return await achat_llama(self.model_name,messages)
    
    def gen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ) -> Union[List[str], str]:
        return _run_async(self.agen(messages, max_tokens, temperature, num_comps))