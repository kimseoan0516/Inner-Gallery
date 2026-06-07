import sys
import os
import google.generativeai as genai
from PIL import Image

def main():
    image_path = "C:/Users/Home/.gemini/antigravity/brain/3c3900cd-91a6-405c-bcfa-7dfbe7e044d0/media__1780506547250.png"
    if not os.path.exists(image_path):
        print("Image not found")
        return
        
    img = Image.open(image_path)
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content([
        img, 
        "Describe this UI screenshot in detail. What text is visible? What sections are there? Are there any sections called '마음배경' or '마음색'? Does it show '제목' (title), '감정 키워드' (emotion keywords), and '느낀점' (note)?"
    ])
    print(response.text)

if __name__ == "__main__":
    main()
