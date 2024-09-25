"""Fill in a module description here"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['FastData']

# %% ../nbs/00_core.ipynb 3
import concurrent.futures

from claudette import *
from fastcore.utils import *
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm

# %% ../nbs/00_core.ipynb 4
class FastData:
    def __init__(self, calls: int = 100, period: int = 60):
        self.set_rate_limit(calls, period)

    def set_rate_limit(self, calls: int, period: int):
        """Set a new rate limit."""
        @sleep_and_retry
        @limits(calls=calls, period=period)
        def rate_limited_call(model: str, prompt: str, response_model, sp: str):
            chat = Chat(
                model,
                sp=sp,
                tools=[response_model],
                tool_choice={'response_model': response_model},
            )
            chat(prompt, temp=1)
            return chat.last_tool_result.content
        
        self._rate_limited_call = rate_limited_call

    def generate(self, 
                 prompt_template: str, 
                 inputs: list[dict], 
                 response_model, 
                 model: str = "claude-3-haiku-20240307",
                 sp: str = "You are a helpful assistant.",
                 max_workers: int = 64) -> list[dict]:
        
        def process_input(input_data):
            try:
                prompt = prompt_template.format(**input_data)
                response = self._rate_limited_call(
                    model=model,
                    prompt=prompt,
                    response_model=response_model,
                    sp=sp
                )
                return response
            except Exception as e:
                print(f"Error processing input: {e}")
                return None

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_input, input_data) for input_data in inputs]
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(inputs)):
                result = future.result()
                results.append(result)
        
        return results