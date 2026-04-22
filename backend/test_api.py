import google.generativeai as genai

API_KEY = "AIzaSyAeFenCSId5BMMUoUVA9ZFKvPmJqwE6xHo"
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content("Say hello")
print("SUCCESS:", response.text)