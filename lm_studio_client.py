from openai import OpenAI


class LMStudioClient:
    def __init__(self, base_url="http://localhost:1234/v1", api_key="lm-studio", model=None):
        """
        Initialize LMStudioClient.

        Args:
            base_url (str): Base URL of the LM Studio API.
            api_key (str): API key for authentication.
            model (str, optional): Model name to use for requests.
        """
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def set_model(self, model_name):
        """
        Set the model name for requests.

        Args:
            model_name (str): Name of the model to use.
        """
        self.model = model_name

    def chat(self, messages, temperature=0.2, max_tokens=2048):
        """
        Sends a chat completion request to the LM Studio API.

        Args:
            messages (list): List of message dicts for the conversation.
            temperature (float, optional): Sampling temperature.
            max_tokens (int, optional): Maximum number of tokens in the response.

        Returns:
            str: The content of the model's response message.

        Raises:
            ValueError: If no model is set.
        """
        if self.model is None:
            raise ValueError("Kein Modell gesetzt. Mit set_model() definieren.")
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content


if __name__ == "__main__":
    lm = LMStudioClient()
    lm.set_model("openai/gpt-oss-20b")  # Beispielmodellname
    response = lm.chat([
        {"role": "user", "content": "Was ist die Hauptstadt von Deutschland?"}
    ])
    print("Antwort:", response)
