from google import genai
import json

client = genai.Client(api_key="AIzaSyDqQd5EtOA62Qte3pKcVeZ1HHkoV32r9Eo")

def convert_post(text):
    prompt = f"""
You are converting Reddit posts into VECTOR DATABASE CHUNKS.

RULES (DO NOT CHANGE):
- Extract ONLY FAU-related meaning
- Remove ads, usernames, timestamps
- Split into atomic ideas (1 idea per entry)
- Assign correct topic:
  PARKING, HOUSING, ACADEMICS, CAMPUS_LIFE, ADMIN
- If not relevant, return []

OUTPUT FORMAT (STRICT JSON ONLY):
[
  {{
    "topic": "PARKING",
    "type": "fact | opinion | strategy | edge_case",
    "text": "clean rewritten sentence",
    "tags": ["keyword1", "keyword2"]
  }}
]

TEXT:
{text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        return json.loads(response.text)

    except Exception as e:
        print("Error:", e)
        return []


def main():
    input_file = "reddit_input.txt"
    output_file = "vector_dataset.jsonl"

    with open(input_file, "r", encoding="utf-8") as f:
        raw = f.read()

    posts = [p.strip() for p in raw.split("---") if p.strip()]

    with open(output_file, "w", encoding="utf-8") as out:

        for i, post in enumerate(posts):
            print(f"Processing {i+1}/{len(posts)}")

            chunks = convert_post(post)

            for j, chunk in enumerate(chunks):
                record = {
                    "id": f"post_{i}_chunk_{j}",
                    "topic": chunk.get("topic", "UNKNOWN"),
                    "type": chunk.get("type", "fact"),
                    "text": chunk.get("text", ""),
                    "tags": chunk.get("tags", [])
                }

                out.write(json.dumps(record) + "\n")

    print("DONE ->", output_file)


if __name__ == "__main__":
    main()