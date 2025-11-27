import json
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        """
        Handle WebSocket connection
        """
        try:
            # User is authenticated via middleware
            self.user = self.scope['user']
            
            if self.user.is_anonymous:
                # Send an error message before closing the connection
                self.accept() # Must accept before sending a message
                self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication failed. Please provide a valid token.'
                }))
                self.close(code=4001)
                return

            self.accept()
            
            # Send welcome message
            self.send(text_data=json.dumps({
                'type': 'connection',
                'message': 'Connected successfully. You can now send queries.'
            }))

        except Exception as e:
            self.close(code=4000)

    def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        if hasattr(self, 'user') and not self.user.is_anonymous:
            print(f"WebSocket disconnected: {self.user.username}")


    def receive(self, text_data):
        self.send(text_data=f"Echo: {text_data}")