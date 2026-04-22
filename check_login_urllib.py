import urllib.request
import urllib.parse
import http.cookiejar

def check_login():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    login_url = 'http://127.0.0.1:5000/login'
    target_url = 'http://127.0.0.1:5000/recent_donations'
    
    # Login
    print("Logging in...")
    data = urllib.parse.urlencode({'email': 'test@example.com', 'password': 'password'}).encode()
    try:
        response = opener.open(login_url, data=data)
        print(f"Login status: {response.getcode()}")
        print(f"Login url: {response.geturl()}")
        
        if 'dashboard' in response.geturl():
            print("Login successful, redirected to dashboard.")
        elif 'login' in response.geturl():
            print("Login failed, stayed on login page.")
    except Exception as e:
        print(f"Login error: {e}")
        return

    # Visit target
    print(f"Visiting {target_url}...")
    try:
        response = opener.open(target_url)
        print(f"Target status: {response.getcode()}")
        print(f"Target url: {response.geturl()}")
        
        content = response.read().decode('utf-8')
        if 'recent_donations' in response.geturl() or 'Recent Donations' in content:
            print("Successfully accessed recent_donations.")
        else:
            print("Failed to access recent_donations content.")
            
    except urllib.error.HTTPError as e:
        print(f"HTTP Error on recent_donations: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"Error accessing recent_donations: {e}")

if __name__ == "__main__":
    check_login()
