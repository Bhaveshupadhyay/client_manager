import requests
import json
import sys

def main():
    # Get base URL from user
    base_url = input("Enter base URL (default: http://localhost:8000): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"

    # Remove trailing slash if present
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    # Get client name from user
    client_name = input("Enter your client name (default: Anonymous): ").strip()
    if not client_name:
        client_name = "Anonymous"

    print(f"\nChat client started. Connecting to {base_url}")
    print(f"Client name: {client_name}")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            # Check for exit commands
            if user_input.lower() in ['exit', 'quit']:
                print("Ending chat session. Goodbye!")
                break

            # Skip empty messages
            if not user_input:
                continue

            # Prepare request payload
            payload = {
                "message": user_input,
                "client_name": client_name
            }

            # Send request to chat endpoint
            response = requests.post(
                f"{base_url}/",
                json=payload,
                timeout=30  # 30 second timeout
            )

            # Check if request was successful
            response.raise_for_status()

            # Parse response
            response_data = response.json()
            bot_message = response_data.get('message', 'No message received')

            # Display bot response
            print(f"Bot: {bot_message}\n")

        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Please check if the server is running and the URL is correct.\n")
        except requests.exceptions.Timeout:
            print("Error: Request timed out. Please try again.\n")
        except requests.exceptions.HTTPError as e:
            print(f"Error: Server returned an error: {e}\n")
        except json.JSONDecodeError:
            print("Error: Invalid response from server. Expected JSON.\n")
        except KeyboardInterrupt:
            print("\nEnding chat session. Goodbye!")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}\n")

if __name__ == "__main__":
    main()