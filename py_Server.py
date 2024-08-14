import asyncio
import websockets
import logging
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
import socket  # Import socket to get the IP address

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

clients = {}  # Dictionary to store client ID and WebSocket pairs

import asyncio
import websockets
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

clients = {}  # Dictionary to store client ID and WebSocket pairs
streams = {}  # Dictionary to store active streams and their current values

class WebSocketServer:
    def __init__(self):
        self.server = None
        self.loop = None
        self.should_stop = False

    async def register(self, websocket):
        await websocket.send("REQUEST_ID")  # Server requests client ID
        try:
            client_id = await websocket.recv()  # Receive the client ID from the client
            clients[client_id] = websocket
            logging.info(f"New client connected: ID {client_id}")

            async for message in websocket:
                logging.info(f"Received message from ID {client_id}: {message}")
                await self.handle_message(client_id, message)
        except websockets.ConnectionClosed as e:
            logging.warning(f"Connection closed: {e}")
        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            clients.pop(client_id, None)
            logging.info(f"Client disconnected: ID {client_id}")

    async def handle_message(self, client_id, message):
        try:
            data = json.loads(message)
            command = data.get("command")

            if command == "send_to_client":
                target_id = data.get("target_id")
                target_client = clients.get(target_id)
                if target_client:
                    await target_client.send(json.dumps(data))
                    logging.info(f"Message from {client_id} sent to {target_id}")
                else:
                    logging.warning(f"Client {target_id} not found.")

            elif command == "start_stream":
                stream_name = data.get("stream_name")
                streams[stream_name] = None  # Initialize the stream with no data
                logging.info(f"Stream '{stream_name}' started by {client_id}")
                app.refresh_stream_dropdown()  # Refresh the dropdown to show the new stream

            elif command == "stream_data":
                stream_name = data.get("stream_name")
                stream_data = data.get("data")
                streams[stream_name] = stream_data
                logging.info(f"Received stream data for '{stream_name}' from {client_id}: {stream_data}")
                if app.stream_dropdown.get() == stream_name:
                    app.update_stream_display(stream_name)

            elif command == "request_stream_data":
                stream_name = data.get("stream_name")
                if stream_name in streams:
                    current_data = streams.get(stream_name)
                    response = {"command": "stream_data", "stream_name": stream_name, "data": current_data}
                    await clients[client_id].send(json.dumps(response))
                    logging.info(f"Sent current stream data for '{stream_name}' to {client_id}")
                else:
                    logging.warning(f"Stream '{stream_name}' not found.")

            elif command == "close_stream":
                stream_name = data.get("stream_name")
                if stream_name in streams:
                    streams.pop(stream_name, None)
                    logging.info(f"Stream '{stream_name}' closed by {client_id}")
                    app.refresh_stream_dropdown()  # Refresh the dropdown to remove the closed stream

            else:
                logging.warning(f"Unknown command from {client_id}: {command}")

        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON message from {client_id}: {message}")


    async def send_message_to_client(self, client_id, message):
        client = clients.get(client_id)
        if client:
            await client.send(message)
            logging.info(f"Sent message to ID {client_id}: {message}")
        else:
            logging.warning(f"Client ID {client_id} not found.")

    async def main(self):
        logging.info("Server started, waiting for clients to connect...")
        self.server = await websockets.serve(self.register, "0.0.0.0", 8080)
        try:
            while not self.should_stop:
                await asyncio.sleep(1)
        finally:
            logging.info("Server stopping, disconnecting all clients...")
            await self.disconnect_all_clients()
            self.server.close()
            await self.server.wait_closed()
            logging.info("Server has been stopped.")

    async def disconnect_all_clients(self):
        if clients:
            logging.info("Disconnecting all clients...")
            disconnect_tasks = []
            for client_id, websocket in list(clients.items()):
                await websocket.send("SERVER_CLOSING")
                disconnect_tasks.append(websocket.close())
            await asyncio.gather(*disconnect_tasks)
            clients.clear()
            logging.info("All clients have been disconnected.")

    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.should_stop = False
        try:
            self.loop.run_until_complete(self.main())
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    def stop(self):
        self.should_stop = True
        if self.server is not None:
            asyncio.run_coroutine_threadsafe(self.disconnect_all_clients(), self.loop).result()
            self.server.close()


    async def main(self):
        logging.info("Server started, waiting for clients to connect...")
        self.server = await websockets.serve(self.register, "0.0.0.0", 8080)
        try:
            while not self.should_stop:
                await asyncio.sleep(1)
        finally:
            logging.info("Server stopping, disconnecting all clients...")
            await self.disconnect_all_clients()  # Disconnect all clients before closing the server

            logging.info("All clients disconnected, closing server...")
            self.server.close()
            logging.info("Server socket closed, waiting for server to finish closing...")

            try:
                await asyncio.wait_for(self.server.wait_closed(), timeout=1.0)  # Add timeout to server closure
                logging.info("Server has been stopped successfully.")
            except asyncio.TimeoutError:
                logging.error("Timeout while waiting for server to close.")
                logging.info("Forcibly stopping the event loop and cancelling all tasks...")

                # Forcefully stop the event loop and cancel all tasks
                tasks = asyncio.all_tasks(self.loop)
                for task in tasks:
                    logging.info(f"Cancelling task: {task}")
                    task.cancel()

                logging.info("Stopping the event loop...")
                self.loop.stop()  # Attempt to stop the event loop
                logging.info("Event loop stopped.")
            except Exception as e:
                logging.error(f"Error while closing server: {e}")

            finally:
                # Attempt to clean up and close the event loop completely
                if not self.loop.is_closed():
                    logging.info("Closing the event loop forcefully...")
                    self.loop.close()
                    logging.info("Event loop closed.")



    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.should_stop = False
        try:
            self.loop.run_until_complete(self.main())
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    def stop(self):
        self.should_stop = True
        if self.server is not None:

            # Now, safely close the server
            self.server.close()



def get_ip_address():
    """Get the server's IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.254.254.254", 1))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "127.0.0.1"  # Default to localhost if unable to get IP
    finally:
        s.close()
    return ip_address

server = WebSocketServer()

class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WebSocket Server")

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Server control buttons
        self.start_button = tk.Button(self.left_frame, text="Start Server", command=self.start_server)
        self.start_button.pack()

        self.stop_button = tk.Button(self.left_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack()

        # Server log
        self.log_label = tk.Label(self.left_frame, text="Server Log")
        self.log_label.pack()

        self.log_text = scrolledtext.ScrolledText(self.left_frame, state='disabled', height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Client management
        self.clients_label = tk.Label(self.right_frame, text="Connected Clients")
        self.clients_label.pack()

        self.clients_list = tk.Listbox(self.right_frame)
        self.clients_list.pack(fill=tk.BOTH, expand=True)

        # Message input to clients
        self.message_label = tk.Label(self.right_frame, text="Input message to broadcast:")
        self.message_label.pack()

        self.message_entry = tk.Entry(self.right_frame)
        self.message_entry.pack(fill=tk.X)
        self.message_entry.bind('<Return>', self.broadcast_message)

        # Dropdown and display area for streaming data
        self.stream_label = tk.Label(self.right_frame, text="Select Stream to Monitor:")
        self.stream_label.pack()

        self.stream_dropdown = tk.StringVar(self.right_frame)
        self.stream_dropdown.set("Select Stream")  # Default value

        # Initialize the dropdown with a placeholder
        self.stream_menu = tk.OptionMenu(self.right_frame, self.stream_dropdown, "Select Stream", *streams.keys(), command=self.update_stream_display)
        self.stream_menu.pack(fill=tk.X)

        self.stream_data_label = tk.Label(self.right_frame, text="Current Stream Data:")
        self.stream_data_label.pack()

        self.stream_data_display = tk.Label(self.right_frame, text="", wraplength=300)
        self.stream_data_display.pack(fill=tk.BOTH, expand=True)

        # Resend toggle
        self.resend_button = tk.Button(self.right_frame, text="Disable Resend", command=self.toggle_resend)
        self.resend_button.pack()

    def start_server(self):
        self.server_thread = Thread(target=server.start)
        self.server_thread.start()
        self.log_message("Server starting...")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_server(self):
        server.stop()
        self.server_thread.join()
        self.log_message("Server stopped.")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def log_message(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.config(state='disabled')
        self.log_text.yview(tk.END)

    def add_client(self, client_id):
        self.clients_list.insert(tk.END, f"Client ID {client_id}")

    def remove_client(self, client_id):
        clients = self.clients_list.get(0, tk.END)
        for i, c in enumerate(clients):
            if c == f"Client ID {client_id}":
                self.clients_list.delete(i)
                break

    def broadcast_message(self, event):
        message = self.message_entry.get()
        self.message_entry.delete(0, tk.END)
        asyncio.run_coroutine_threadsafe(server.notify_clients(message), server.loop)
        self.log_message(f"Broadcasted message: {message}")

    def update_stream_display(self, selected_stream):
        if selected_stream in streams:
            current_data = streams[selected_stream]
            self.stream_data_display.config(text=current_data)
        else:
            self.stream_data_display.config(text="Stream not found.")

    def refresh_stream_dropdown(self):
        menu = self.stream_menu["menu"]
        menu.delete(0, "end")
        for stream_name in streams.keys():
            menu.add_command(label=stream_name, command=lambda value=stream_name: self.update_stream_display(value))

    def toggle_resend(self):
        global resend_messages
        resend_messages = not resend_messages
        if resend_messages:
            self.resend_button.config(text="Disable Resend")
            self.log_message("Resend messages enabled.")
        else:
            self.resend_button.config(text="Enable Resend")
            self.log_message("Resend messages disabled.")

app = None

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApp(root)
    root.mainloop()
