
import socket
import threading

def handle_client(client_socket):
    try:
        # Send initial greeting
        client_socket.send(b'220 localhost Python SMTP Fake Server\r\n')
        
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            
            command = data.decode('utf-8', errors='ignore').strip()
            print(f"Received: {command}")
            
            if command.upper().startswith('HELO') or command.upper().startswith('EHLO'):
                client_socket.send(b'250 Hello\r\n')
            elif command.upper().startswith('MAIL FROM'):
                client_socket.send(b'250 OK\r\n')
            elif command.upper().startswith('RCPT TO'):
                client_socket.send(b'250 OK\r\n')
            elif command.upper().startswith('DATA'):
                client_socket.send(b'354 End data with <CR><LF>.<CR><LF>\r\n')
                # Read data until .
                email_content = b""
                while True:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    email_content += chunk
                    if b'\r\n.\r\n' in chunk:
                        break
                
                print("End of data received.")
                
                # Save to file
                try:
                    with open("sent_emails.txt", "ab") as f:
                        f.write(b"\n" + ("="*50).encode() + b"\n")
                        f.write(b"NEW EMAIL RECEIVED:\n")
                        f.write(email_content)
                        f.write(b"\n" + ("="*50).encode() + b"\n")
                    print("Email saved to sent_emails.txt")
                except Exception as e:
                    print(f"Error saving to file: {e}")
                
                client_socket.send(b'250 OK\r\n')
            elif command.upper().startswith('QUIT'):
                client_socket.send(b'221 Bye\r\n')
                break
            else:
                client_socket.send(b'500 Unknown command\r\n')
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def run_server(port=1025):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', port))
    server.listen(5)
    print(f"Mock SMTP Server listening on port {port}...")
    
    while True:
        client, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

if __name__ == '__main__':
    run_server()
