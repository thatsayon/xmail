# from transformers import pipeline

# generator = pipeline("text-generation", model="gpt2")

# def generate_draft(email_text: str) -> str:
#     prompt = f"Reply to the following email in a professional and polite manner. Keep the tone of the email. Do not add any extra information. Do not add any emojis. Do not add any hashtags. Do not add any links. Do not add any emojis. If the email is about a sensitive topic, please keep the tone polite and professional. If the email is not about a sensitive topic, please keep the tone casual and friendly. Please keep the tone of the email. Please keep the email short. The email is: {email_text}"
#     response = generator(prompt, max_length=1000, do_sample=True)[0]["generated_text"]
#     return response.replace(prompt, "").strip()

from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load pre-trained GPT-2 model and tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

def generate_draft_response(email_body: str) -> str:
    """
    Generates a short, clean, and directly sendable response to a customer email.
    """

    # Clear instruction prompt for generation
    prompt = (
        f"Respond to this customer inquiry politely and helpfully. "
        f"Keep it short, clear, and appropriate to the tone. "
        f"Do not add emojis, hashtags, links, or unnecessary text. "
        f"The email is: {email_body.strip()}"
    )

    # Encode prompt
    inputs = tokenizer.encode(prompt, return_tensors="pt", max_length=512, truncation=True)

    # Calculate available generation space
    max_length = tokenizer.model_max_length
    available_length = max_length - inputs.shape[1]

    # Generate output
    outputs = model.generate(
        inputs,
        max_length=inputs.shape[1] + available_length,
        num_return_sequences=1,
        no_repeat_ngram_size=2,
        pad_token_id=tokenizer.eos_token_id,
    )

    # Decode and isolate the response text only (without prompt)
    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = full_text.replace(prompt, "").strip()

    return clean_response(response)

def clean_response(text: str) -> str:
    """
    Post-process the response to remove model artifacts and irrelevant content.
    """
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if line and not line.lower().startswith("the email is"):
            cleaned.append(line)

    return " ".join(cleaned).strip()
