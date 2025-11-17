import json
from channels.generic.websocket import WebsocketConsumer
import vosk
import queue

# Load vosk model once
model = vosk.Model("vosk-model-small-en-us-0.15")

class InterviewConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.q = queue.Queue()
        self.recognizer = vosk.KaldiRecognizer(model, 16000)

    def receive(self, text_data=None, bytes_data=None):
        if bytes_data:  # receiving raw audio
            if self.recognizer.AcceptWaveform(bytes_data):
                result = json.loads(self.recognizer.Result())
                transcript = result.get("text", "")
                self.send(text_data=json.dumps({"transcript": transcript}))
        else:
            self.send(text_data=json.dumps({"message": "No audio received"}))

    def disconnect(self, close_code):
        final_result = json.loads(self.recognizer.FinalResult())
        transcript = final_result.get("text", "")
        self.send(text_data=json.dumps({"final_transcript": transcript}))
