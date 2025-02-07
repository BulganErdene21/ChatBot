import random
import json
import re
import torch
import os
from model import NeuralNet
from nltkUtils import bag_of_words, tokenize
from api_wiki import get_wikipedia_summary
from api_weather import get_weather
from subprocess import call

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
bot_name = "Caffe Bene"
WEATHER_API_KEY = 'b546710a0aec466dbc150610231212'
FILE = "data.pth"

def load_data_and_initialize_model():
    with open('intents.json', 'r', encoding='utf-8') as json_data:
        intents = json.load(json_data)

    data = torch.load(FILE)
    model = NeuralNet(data["input_size"], data["hidden_size"], data["output_size"]).to(DEVICE)
    model.load_state_dict(data["model_state"])
    model.eval()

    return model, intents, data['all_words'], data['tags']

def handle_wikipedia_search(sentence):
    wikipedia_search_patterns = re.compile(r"(search\s(wikipedia|wiki)|wikipedia|wiki)\s*['\"]?([^'\"]*)['\"]?")
    if wikipedia_search_patterns.search(sentence):
        match = wikipedia_search_patterns.search(sentence)
        search_query = match.group(3) if match.group(3) else input(f"{bot_name}: Та Wikipedia-аас ямар мэдээлэл хайхыг хүсэж байна вэ?\n")
        summary = get_wikipedia_summary(search_query)
        return f"{bot_name} Wikipedia Summary for '{search_query}':\n{summary}"
    return None

def handle_weather_search(sentence):
    weather_search_patterns = re.compile(r"(weather|temperature|цаг агаар|Цаг агаар)\s*['\"]?([^'\"]*)['\"]?")
    if weather_search_patterns.search(sentence):
        match = weather_search_patterns.search(sentence)
        location = match.group(2) if match.group(2) else input(f"{bot_name}: Та ямар хотын цаг агаарыг мэдэхийг хүсэж байна вэ?\n")
        weather_info = get_weather(WEATHER_API_KEY, location)
        return f"{weather_info}"
    return None

def process_message(model, sentence, intents, all_words, tags):
    sentence = tokenize(sentence)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(DEVICE)
    output = model(X)
    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                """
               if tag == intent["tag"] and tag in ["location"]:
                   
                   return get_user_location() 
                """
                return random.choice(intent['responses'])
    return "Би ойлгохгүй байна..."

def chat():
    model, intents, all_words, tags = load_data_and_initialize_model()
    print("Let's chat! (type 'quit' to exit)")
    while True:
        sentence = input("You: ")
        if sentence.lower() == "quit":
            break
        response = handle_wikipedia_search(sentence) or handle_weather_search(sentence) or process_message(model, sentence, intents, all_words, tags)
        print(f"{bot_name}: {response}")

if __name__ == "__main__":
    chat()
