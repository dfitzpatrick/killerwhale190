from bot.pokemon.trained_model import PokemonTFLiteGuesser
import pytest
import pathlib
base_model_dir = pathlib.Path(__file__).parents[1] / 'bot/pokemon/models'
model_path = str(base_model_dir / 'final.tflite')
names_path = str(base_model_dir / 'final.txt')

def test_process_image():
    guesser = PokemonTFLiteGuesser(model_path=model_path, names_path=names_path)
    sample_image = pathlib.Path(__file__).parent / 'pokemon-pawmi.png'
    with sample_image.open(mode='rb') as f:
        data = f.read()
    result = guesser.process_image(data)
    assert False