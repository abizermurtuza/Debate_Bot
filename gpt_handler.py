from openai import OpenAI
from config import OPENAI_API_KEY, GPT_MODEL, SYSTEM_PROMPT

class GPTHandler:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.position = None  # 'for' or 'against'
        self.motion = None

    def generate_response(self, user_input, round_number, position=None, motion=None, is_closing=False):
        if position:
            self.position = position
        if motion:
            self.motion = motion

        # Handle opening arguments or rebuttals
        if user_input is None and round_number == 1:
            # Generate opening arguments
            prompt = f"As the {self.position} side, present your opening arguments for the motion: '{self.motion}'"
        elif round_number >= 1:
            # Generate rebuttal
            if is_closing:
                prompt = f"Provide a strong closing statement for the {self.position} side of the motion: '{self.motion}'. Summarize your main points and refute the opponent's arguments in around 800 words."
            else:
                prompt = f"Provide counter arguments to the following argument within 800 words: {user_input}"
        else:
            prompt = f"Continue the debate on the motion: '{self.motion}'"

        self.conversation_history.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=self.conversation_history,
            max_tokens=5000,
            temperature=0.7
        )

        rebuttal = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": rebuttal})
        return rebuttal

    def set_debate_context(self, position, motion):
        self.position = position
        self.motion = motion

    def reset_conversation(self):
        self.conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.position = None
        self.motion = None
