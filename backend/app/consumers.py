import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from fyers_apiv3.FyersWebsocket import data_ws
from .services import FyersTokenService

class StockPriceConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fyers_socket = None
        self.access_token = None
        self.connected = False
        self._loop = None  

    async def connect(self):
        print("Connecting to WebSocket")
        await self.accept()
        self._loop = asyncio.get_running_loop()  # Store the event loop
        
        try:
            # Get the access token
            self.access_token = await FyersTokenService.get_access_token()
            print("Access token obtained:", self.access_token)
            
            if not self.access_token:
                print("No access token received")
                await self.send_error('Failed to obtain access token')
                await self.close()
                return
                
            # Initialize Fyers WebSocket with SYNCHRONOUS callbacks
            self.fyers_socket = data_ws.FyersDataSocket(
                access_token=self.access_token,
                log_path="",
                litemode=False,
                write_to_file=False,
                reconnect=True,
                on_connect=self.on_open_sync,  # Synchronous callback
                on_close=self.on_close_sync,   # Synchronous callback
                on_error=self.on_error_sync,   # Synchronous callback
                on_message=self.on_message_sync # Synchronous callback
            )
            
            print("Connecting to Fyers WebSocket")
            # Run the blocking connect in a separate thread
            await self.run_in_thread(self.fyers_socket.connect)
            print("Connection request sent to Fyers WebSocket")
            
        except Exception as e:
            print(f"Error during connection: {e}")
            await self.send_error(f'Connection error: {str(e)}')
            await self.close()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnecting with code {close_code}")
        if self.fyers_socket:
            try:
                # Run the blocking close in a separate thread
                await self.run_in_thread(self.fyers_socket.close_connection)
            except Exception as e:
                print(f"Error during disconnect: {e}")

    async def run_in_thread(self, func, *args):
        """Run blocking functions in a separate thread"""
        return await self._loop.run_in_executor(None, lambda: func(*args))

    # Synchronous callbacks for Fyers WebSocket
    def on_message_sync(self, message):
        """Called from Fyers thread - must schedule async work"""
        print(f"Message received from Fyers: {message}")
        asyncio.run_coroutine_threadsafe(self.on_message_async(message), self._loop)

    def on_error_sync(self, error):
        """Called from Fyers thread - must schedule async work"""
        print(f"Error from Fyers: {error}")
        asyncio.run_coroutine_threadsafe(self.on_error_async(error), self._loop)
    
    def on_close_sync(self):
        """Called from Fyers thread - must schedule async work"""
        print("Fyers WebSocket connection closed")
        self.connected = False
        asyncio.run_coroutine_threadsafe(self.on_close_async(), self._loop)
    
    def on_open_sync(self):
        """Called from Fyers thread - must schedule async work"""
        print("Fyers WebSocket connection opened")
        self.connected = True
        asyncio.run_coroutine_threadsafe(self.on_open_async(), self._loop)

    # Async methods to handle WebSocket communication
    async def on_message_async(self, message):
        print(f"Sending message to client: {message}")
        try:
            await self.send(text_data=json.dumps({
                'type': 'data_update',
                'message': message,
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            print(f"Error sending message to client: {e}")
            await self.send_error(f"Failed to process market data: {str(e)}")

    async def on_error_async(self, error):
        print(f"Sending error to client: {error}")
        await self.send_error(str(error))

    async def on_close_async(self):
        print("Sending close notification to client")
        try:
            await self.send(text_data=json.dumps({
                'type': 'connection_closed',
                'message': 'Fyers WebSocket connection closed'
            }))
        except Exception as e:
            print(f"Error sending close notification: {e}")

    async def on_open_async(self):
        print("Fyers connection open, subscribing to symbols")
        try:
            data_type = "SymbolUpdate"
            symbols = ['NSE:ADANIENT-EQ']
            
            # Create a lambda function to properly pass arguments
            subscribe_fn = lambda: self.fyers_socket.subscribe(
                symbols=symbols,
                data_type=data_type
            )
            
            await self.run_in_thread(subscribe_fn)
            
            await self.send(text_data=json.dumps({
                'type': 'subscribed',
                'symbols': symbols,
                'data_type': data_type
            }))
            
        except Exception as e:
            print(f"Error during subscription: {e}")
            await self.send_error(f'Subscription error: {str(e)}')

    async def send_error(self, message):
        """Helper to send error messages"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': message
            }))
        except Exception as e:
            print(f"Failed to send error message: {e}")

    async def receive(self, text_data):
        print(f"Received message from client: {text_data}")
        try:
            data = json.loads(text_data)
            
            if not self.fyers_socket or not self.connected:
                await self.send_error('Not connected to Fyers WebSocket')
                return
                
            action = data.get('action')
            
            if action == 'subscribe' and 'symbols' in data:
                symbols = data['symbols']
                data_type = data.get('data_type', 'SymbolUpdate')

                print("-------------data type =========",data_type)

                data_type = 'SymbolUpdate'
                
                # Create a lambda function to properly pass arguments
                subscribe_fn = lambda: self.fyers_socket.subscribe(
                    symbols=symbols,
                    data_type=data_type
                )
                
                await self.run_in_thread(subscribe_fn)
                
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'symbols': symbols,
                    'data_type': data_type
                }))
                
            elif action == 'unsubscribe' and 'symbols' in data:
                symbols = data['symbols']
                data_type = data.get('data_type', 'SymbolUpdate')
                
                # Create a lambda function to properly pass arguments
                unsubscribe_fn = lambda: self.fyers_socket.unsubscribe(
                    symbols=symbols,
                    data_type=data_type
                )
                
                await self.run_in_thread(unsubscribe_fn)
                
                await self.send(text_data=json.dumps({
                    'type': 'unsubscribed',
                    'symbols': symbols,
                    'data_type': data_type
                }))
                
        except Exception as e:
            print(f"Error processing client message: {e}")
            await self.send_error(f'Error processing request: {str(e)}')