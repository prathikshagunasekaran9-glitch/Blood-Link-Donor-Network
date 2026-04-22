import requests

def check_login():
    session = requests.Session()
    login_url = 'http://127.0.0.1:5000/login'
    target_url = 'http://127.0.0.1:5000/recent_donations'
    
    # Login
    print("Logging in...")
    response = session.post(login_url, data={'email': 'test@example.com', 'password': 'password'})
    print(f"Login status: {response.status_code}")
    print(f"Login url: {response.url}")
    
    if 'dashboard' in response.url:
        print("Login successful, redirected to dashboard.")
    elif 'login' in response.url:
        print("Login failed, stayed on login page.")
        # print(response.text)
    
    # Visit target
    print(f"Visiting {target_url}...")
    response = session.get(target_url)
    print(f"Target status: {response.status_code}")
    print(f"Target url: {response.url}")
    
    if response.status_code == 200 and 'recent_donations' in response.url:
        print("Successfully accessed recent_donations.")
        # print(response.text[:500])
    elif response.status_code == 500:
        print("Server error (500) on recent_donations.")
        print(response.text)
    else:
        print("Failed to access recent_donations.")

if __name__ == "__main__":
    check_login()
