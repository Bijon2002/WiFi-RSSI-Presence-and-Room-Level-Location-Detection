import config
import requests

def test_telegram():
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    
    print(f"Token: {token}")
    print(f"Chat ID: {chat_id}")
    
    if not token or not chat_id:
        print("Missing credentials!")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, data={"chat_id": chat_id, "text": "Test message from WiFi Tracker!"})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

if __name__ == "__main__":
    test_telegram()
