import logging
import sys
from typing import Optional

import cv2
import numpy as np
from tensorflow import lite as tflite

from .protocols import PokemonGuess

log = logging.getLogger(__name__)

class PokemonTFLiteGuesser:

    def __init__(self, model_path: str, names_path: str):
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.labels = []

        with open(names_path, 'r') as f:
            self.labels = [l.strip() for l in f.readlines()]

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def resize_image(self, image_data: bytes):
        # Tried to use imdecode instead but was giving errors. This is clients code which
        # uses a local file path so I am just going to mock that with a temporary file

        # Clients code indicates this size required
        image_np = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (224, 224))
        return img

    def process_image(self, image_data: bytes) -> Optional[PokemonGuess]:
        try:
            img = self.resize_image(image_data)
            inputs = np.array(np.expand_dims(img, 0)).astype('uint8')
            inputs_idx = self.input_details[0]['index']
            self.interpreter.set_tensor(inputs_idx, inputs)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            pred = np.squeeze(output_data)
            highest_pred_loc = np.argmax(pred)
            pokemon_name = self.labels[highest_pred_loc]
        except IndexError:
            return
        except:
            log.error(sys.exc_info()[0])
        else:
            return PokemonGuess(name=pokemon_name, data=image_data)


