import openai
openai.api_key = "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"

# completion = openai.ChatCompletion.create(
#   model="gpt-3.5-turbo",
#   messages=[
#     {"role": "user", "content": "How bug is USA?"}
#   ]
# )

# Write code - meme generator
# Generate meme from text using openai
# Text to speech


# print(completion.choices[0].message)


completion = openai.Image.create(
  prompt="Apple on a table, 3D render.",
  n=2,
  size="1024x1024"
)

print(completion)

