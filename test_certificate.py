import urllib.request
import urllib.parse
import http.cookiejar

def test_certificate():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    login_url = 'http://127.0.0.1:5000/login'
    cert_url = 'http://127.0.0.1:5000/certificate/49' # Assuming ID 49 exists and is completed
    
    # Login
    print("Logging in...")
    data = urllib.parse.urlencode({'email': 'test@example.com', 'password': 'password'}).encode()
    try:
        opener.open(login_url, data=data)
        print("Login successful.")
    except Exception as e:
        print(f"Login error: {e}")
        return

    # Download Certificate
    print(f"Downloading certificate from {cert_url}...")
    try:
        response = opener.open(cert_url)
        print(f"Status: {response.getcode()}")
        headers = response.info()
        print(f"Content-Type: {headers['Content-Type']}")
        
        content = response.read()
        if content.startswith(b'%PDF'):
            print("Success: Response is a PDF file.")
            with open('test_certificate.pdf', 'wb') as f:
                f.write(content)
            print("Saved to test_certificate.pdf")
        else:
            print("Error: Response is not a PDF.")
            print(content[:100])
            
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_certificate()
